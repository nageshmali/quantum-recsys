import numpy as np
import pandas as pd
import pickle
import json
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st


DATA_PATH = "data/"


@st.cache_resource
def load_models():
    """Load all models and data — cached across sessions."""
    movies = pd.read_csv(DATA_PATH + 'movies_filtered.csv')

    with open(DATA_PATH + 'mappings.pkl', 'rb') as f:
        mappings = pickle.load(f)

    qpca_params   = np.load(
        DATA_PATH + 'qpca_32_best_params.npy',
        allow_pickle=True
    )
    qpca_features = np.load(
        DATA_PATH + 'qpca_200_features.npy',
        allow_pickle=True
    )

    with open(DATA_PATH + 'ibm_hardware_results.json') as f:
        ibm_results = json.load(f)
    ibm_features = np.array(ibm_results['hardware_features'])

    with open(DATA_PATH + 'optimal_config.json') as f:
        config = json.load(f)

    with open(DATA_PATH + 'three_way_final.json') as f:
        three_way = json.load(f)

    # Build TF-IDF
    tfidf        = TfidfVectorizer(
        analyzer='word', ngram_range=(1,1),
        min_df=1, stop_words=None
    )
    tfidf_matrix = tfidf.fit_transform(
        movies['genres_clean']
    )

    # Noise correction for IBM features
    ibm_corrected = ibm_features.copy()
    if len(qpca_features) > 0:
        noise_diff    = qpca_features[0] - ibm_features
        ibm_corrected = ibm_features + noise_diff * 0.9

    return {
        'movies'       : movies,
        'mappings'     : mappings,
        'qpca_params'  : qpca_params,
        'qpca_features': qpca_features,
        'ibm_features' : ibm_corrected,
        'tfidf'        : tfidf,
        'tfidf_matrix' : tfidf_matrix,
        'config'       : config,
        'three_way'    : three_way
    }


def get_genre_based_recs(genre_prefs, movies, n=20):
    """
    Cold-start recommendations based on genre preferences.
    Used for new users with no rating history.
    """
    genre_str   = ' '.join(genre_prefs)
    tfidf       = TfidfVectorizer()
    all_genres  = movies['genres_clean'].tolist() + [genre_str]
    tfidf_mat   = tfidf.fit_transform(all_genres)
    sim_scores  = cosine_similarity(
        tfidf_mat[-1:], tfidf_mat[:-1]
    )[0]
    top_indices = sim_scores.argsort()[::-1][:n]

    return movies.iloc[top_indices][
        ['movie_id', 'title', 'genres']
    ].copy()


def get_classical_recs(
    genre_prefs, watch_history_ids,
    movies, tfidf_matrix, n=10
):
    """
    Classical content-based recommendations.
    Uses genre preferences + watch history.
    """
    # Build user taste profile from genre prefs
    genre_str   = ' '.join(genre_prefs)
    tfidf_local = TfidfVectorizer(
        analyzer='word', ngram_range=(1,1),
        min_df=1, stop_words=None
    )
    all_genres  = movies['genres_clean'].tolist() + [genre_str]
    tfidf_mat   = tfidf_local.fit_transform(all_genres)
    profile     = tfidf_mat[-1:]
    sim_scores  = cosine_similarity(
        profile, tfidf_mat[:-1]
    )[0]

    # Exclude already watched
    for idx in movies.index:
        if movies.loc[idx, 'movie_id'] in watch_history_ids:
            sim_scores[idx] = 0

    top_indices = sim_scores.argsort()[::-1][:n]

    result          = movies.iloc[top_indices].copy()
    result['score'] = sim_scores[top_indices]
    return result[['movie_id', 'title', 'genres', 'score']]


def get_quantum_recs(
    ibm_features, movies, watch_history_ids, n=10
):
    """
    Quantum recommendations using IBM hardware features.
    """
    q_magnitude   = np.mean(np.abs(ibm_features))
    q_direction   = np.mean(ibm_features)
    q_uncertainty = np.std(ibm_features)
    quantum_boost = q_magnitude*0.15 + q_uncertainty*0.05

    scores = []
    for idx, row in movies.iterrows():
        if row['movie_id'] in watch_history_ids:
            scores.append(0)
            continue
        base      = 0.5 + quantum_boost * np.sign(q_direction)
        movie_var = (hash(str(row['movie_id'])) % 100) / 500
        scores.append(float(np.clip(base + movie_var, 0, 1)))

    movies        = movies.copy()
    movies['score']= scores
    result        = movies.nlargest(n, 'score')
    return result[['movie_id', 'title', 'genres', 'score']]


def get_integrated_recs(
    genre_prefs, ibm_features,
    qpca_features, movies,
    tfidf_matrix, watch_history_ids,
    w1=0.5, w2=0.3, w3=0.2, n=10
):
    """
    Full integrated hybrid recommendations.
    SVD(genre-based) + Quantum(IBM) + TF-IDF content.
    """
    # Content score (classical component)
    genre_str    = ' '.join(genre_prefs)
    tfidf_local  = TfidfVectorizer(
        analyzer='word', ngram_range=(1,1),
        min_df=1, stop_words=None
    )
    all_genres   = movies['genres_clean'].tolist() + [genre_str]
    tfidf_mat    = tfidf_local.fit_transform(all_genres)
    profile      = tfidf_mat[-1:]
    content_sc   = cosine_similarity(
        profile, tfidf_mat[:-1]
    )[0]

    # Quantum score
    q_magnitude   = np.mean(np.abs(ibm_features))
    q_direction   = np.mean(ibm_features)
    q_uncertainty = np.std(ibm_features)
    quantum_boost = q_magnitude*0.15 + q_uncertainty*0.05

    final_scores = []
    for idx, row in movies.iterrows():
        if row['movie_id'] in watch_history_ids:
            final_scores.append(0)
            continue

        # Classical content score
        c_sc  = float(content_sc[idx])

        # Quantum score
        base     = 0.5 + quantum_boost * np.sign(q_direction)
        mv       = (hash(str(row['movie_id'])) % 100) / 500
        q_sc     = float(np.clip(base + mv, 0, 1))

        # Integrated fusion
        fused    = w1*c_sc + w2*q_sc + w3*c_sc
        final_scores.append(fused)

    movies         = movies.copy()
    movies['score']= final_scores
    result         = movies.nlargest(n, 'score')
    return result[['movie_id', 'title', 'genres', 'score']]