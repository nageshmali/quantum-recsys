import streamlit as st
import pandas as pd
import json
import os
from database import (
    init_db, get_watch_history,
    add_to_watch_history, add_to_watchlist,
    get_watchlist
)
from auth import show_login_page, show_genre_selection
from recommender import (
    load_models, get_genre_based_recs,
    get_classical_recs, get_quantum_recs,
    get_integrated_recs
)
from tmdb import get_movie_info

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title  = "QuantumRec",
    page_icon   = "🎬",
    layout      = "wide",
    initial_sidebar_state = "expanded"
)

# ── Global CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer     {visibility: hidden;}
    header     {visibility: hidden;}

    /* Global dark background */
    .stApp {background-color: #0d0d0d;}

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #141414;
        border-right: 1px solid #222;
    }

    /* Buttons */
    .stButton > button {
        background-color: #e50914;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background-color: #b20710;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        color: #888;
        font-size: 14px;
    }
    .stTabs [aria-selected="true"] {
        color: #fff;
        border-bottom: 2px solid #e50914;
    }

    /* Input fields */
    .stTextInput > div > div > input {
        background-color: #2a2a2a;
        color: white;
        border: 1px solid #444;
        border-radius: 6px;
    }

    /* Movie card */
    .movie-card {
        background    : #1a1a1a;
        border-radius : 10px;
        padding       : 0;
        overflow      : hidden;
        border        : 1px solid #222;
        transition    : transform 0.2s, border-color 0.2s;
        height        : 100%;
    }
    .movie-card:hover {
        transform    : scale(1.03);
        border-color : #e50914;
    }
    .movie-title {
        font-size   : 13px;
        font-weight : 600;
        color       : #fff;
        padding     : 8px 10px 2px;
        white-space : nowrap;
        overflow    : hidden;
        text-overflow: ellipsis;
    }
    .movie-genre {
        font-size : 11px;
        color     : #888;
        padding   : 0 10px 4px;
    }
    .movie-score {
        font-size   : 12px;
        color       : #e50914;
        font-weight : 600;
        padding     : 0 10px 8px;
    }
    .score-badge {
        background    : #e50914;
        color         : white;
        padding       : 2px 8px;
        border-radius : 4px;
        font-size     : 11px;
        font-weight   : 700;
    }
    .metric-card {
        background    : #1a1a1a;
        border        : 1px solid #333;
        border-radius : 10px;
        padding       : 16px;
        text-align    : center;
    }
    .section-title {
        color       : #fff;
        font-size   : 20px;
        font-weight : 700;
        margin      : 20px 0 12px;
        border-left : 4px solid #e50914;
        padding-left: 12px;
    }
    .ibm-badge {
        background    : #0a0a2a;
        border        : 1px solid #3a3a6a;
        border-radius : 8px;
        padding       : 10px 16px;
        color         : #7b68ee;
        font-size     : 13px;
        margin-bottom : 16px;
    }
</style>
""", unsafe_allow_html=True)

# ── Init ──────────────────────────────────────────────────────
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ── Auth gate ─────────────────────────────────────────────────
if not st.session_state.logged_in:
    show_login_page()
    st.stop()

# ── Genre setup for new users ─────────────────────────────────
if st.session_state.get('is_new_user', 0) == 1:
    show_genre_selection()
    st.stop()

# ── Load models ───────────────────────────────────────────────
models = load_models()
movies = models['movies']

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding:16px 0'>
        <div style='font-size:28px; color:#e50914;
                    font-weight:900; letter-spacing:3px'>
            QUANTUMREC
        </div>
        <div style='color:#888; font-size:11px;
                    letter-spacing:1px; margin-top:4px'>
            QUANTUM-CLASSICAL AI
        </div>
    </div>
    <hr style='border-color:#333; margin:8px 0 16px'>
    <div style='color:#aaa; font-size:13px;
                padding:8px 12px; background:#1a1a1a;
                border-radius:8px; margin-bottom:16px'>
        👤 {st.session_state.username}
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["🏠 Home", "🎬 Recommendations",
         "📋 My Watchlist", "📊 Research Dashboard"],
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Sign Out", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ── Get user data ─────────────────────────────────────────────
username       = st.session_state.username
user_data      = st.session_state.user
genre_prefs    = user_data.get('genre_prefs', ['Drama'])
history        = get_watch_history(username, limit=50)
history_ids    = [h[0] for h in history]

# ── Pages ─────────────────────────────────────────────────────

def render_movie_card(movie_row, col, show_score=True):
    """Render a single movie card with poster."""
    with col:
        title    = movie_row['title']
        movie_id = movie_row['movie_id']
        genres   = movie_row.get('genres', '')
        score    = movie_row.get('score', 0)

        info = get_movie_info(title)

        # Poster
        if info['poster_url']:
            st.image(
                info['poster_url'],
                use_container_width=True
            )
        else:
            st.markdown(
                "<div style='height:200px; background:#222;"
                "border-radius:8px; display:flex;"
                "align-items:center; justify-content:center;"
                "color:#555; font-size:32px'>🎬</div>",
                unsafe_allow_html=True
            )

        # Title (truncated)
        display_title = (
            title[:22] + '...' if len(title) > 22 else title
        )
        st.markdown(
            f"<div class='movie-title'>{display_title}</div>"
            f"<div class='movie-genre'>"
            f"{genres.split('|')[0]}</div>",
            unsafe_allow_html=True
        )

        if show_score and score > 0:
            st.markdown(
                f"<div class='movie-score'>"
                f"Score: {score:.3f}</div>",
                unsafe_allow_html=True
            )

        # Buttons
        b1, b2 = st.columns(2)
        with b1:
            if st.button(
                "Watch", key=f"watch_{movie_id}_{title[:5]}",
                use_container_width=True
            ):
                add_to_watch_history(username, movie_id, title)
                if info['tmdb_url']:
                    st.markdown(
                        f"<a href='{info['tmdb_url']}' "
                        f"target='_blank'>"
                        f"<button style='width:100%;background:"
                        f"#e50914;color:white;border:none;"
                        f"padding:8px;border-radius:6px;"
                        f"cursor:pointer'>Open ↗</button></a>",
                        unsafe_allow_html=True
                    )
        with b2:
            if st.button(
                "+ List",
                key=f"wl_{movie_id}_{title[:5]}",
                use_container_width=True
            ):
                add_to_watchlist(username, movie_id, title)
                st.toast(f"Added to watchlist!")


# ── HOME PAGE ─────────────────────────────────────────────────
if page == "🏠 Home":
    st.markdown(f"""
    <div style='padding:24px 0 8px'>
        <h2 style='color:#fff; margin:0'>
            Good evening,
            <span style='color:#e50914'>
            {username}</span> 👋
        </h2>
        <p style='color:#888; margin:4px 0 0'>
            Your personalised quantum-powered recommendations
        </p>
    </div>
    """, unsafe_allow_html=True)

    # IBM badge
    st.markdown("""
    <div class='ibm-badge'>
        ⚛️ Powered by <b>IBM Kingston</b> (ibm_kingston) ·
        156-qubit Heron r2 quantum processor ·
        Job ID: d72htfuv3u3c73eimhn0
    </div>
    """, unsafe_allow_html=True)

    # Top picks
    st.markdown(
        "<div class='section-title'>Top Picks For You</div>",
        unsafe_allow_html=True
    )

    recs = get_integrated_recs(
        genre_prefs,
        models['ibm_features'],
        models['qpca_features'],
        movies, models['tfidf_matrix'],
        history_ids, n=10
    )

    cols = st.columns(5)
    for i, (_, row) in enumerate(recs.head(5).iterrows()):
        render_movie_card(row, cols[i])

    st.markdown("<br>", unsafe_allow_html=True)
    cols2 = st.columns(5)
    for i, (_, row) in enumerate(recs.tail(5).iterrows()):
        render_movie_card(row, cols2[i])

    # Based on genres
    st.markdown(
        f"<div class='section-title'>"
        f"Because You Like "
        f"{', '.join(genre_prefs[:2])}</div>",
        unsafe_allow_html=True
    )

    genre_recs = get_genre_based_recs(
        genre_prefs, movies, n=5
    )
    cols3 = st.columns(5)
    for i, (_, row) in enumerate(genre_recs.iterrows()):
        render_movie_card(row, cols3[i], show_score=False)


# ── RECOMMENDATIONS PAGE ──────────────────────────────────────
elif page == "🎬 Recommendations":
    st.markdown(
        "<h2 style='color:#fff'>Model Comparison</h2>"
        "<p style='color:#888'>Same user — three different "
        "AI systems. See how each thinks differently.</p>",
        unsafe_allow_html=True
    )

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    metrics = [
        (m1, "Integrated P@10", "0.1030", "+44.1%", "#e50914"),
        (m2, "vs Classical",    "0.0715", "baseline","#564d44"),
        (m3, "vs Quantum",      "0.0730", "baseline","#7F77DD"),
        (m4, "IBM Hardware",    "2s",     "validated","#7b68ee"),
    ]
    for col, label, val, sub, color in metrics:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='color:#888;font-size:11px;
                            text-transform:uppercase;
                            letter-spacing:1px'>
                    {label}
                </div>
                <div style='color:{color};font-size:28px;
                            font-weight:700;margin:4px 0'>
                    {val}
                </div>
                <div style='color:#666;font-size:11px'>
                    {sub}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Three columns — one per model
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div style='background:#1a1a1a;border-radius:10px;
                    padding:16px;border:1px solid #333;
                    margin-bottom:16px'>
            <div style='color:#888;font-size:12px;
                        text-transform:uppercase;
                        letter-spacing:1px'>System 1</div>
            <div style='color:#fff;font-size:18px;
                        font-weight:700'>Classical</div>
            <div style='color:#888;font-size:12px'>
                SVD + TF-IDF · P@10: 0.0715
            </div>
        </div>
        """, unsafe_allow_html=True)

        classical_recs = get_classical_recs(
            genre_prefs, history_ids,
            movies, models['tfidf_matrix'], n=6
        )
        for _, row in classical_recs.iterrows():
            info = get_movie_info(row['title'])
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                if info['poster_url']:
                    st.image(
                        info['poster_url'],
                        use_container_width=True
                    )
            with col_txt:
                st.markdown(
                    f"**{row['title'][:30]}**\n\n"
                    f"<span style='color:#888;font-size:11px'>"
                    f"{row['genres'].split('|')[0]}</span>",
                    unsafe_allow_html=True
                )
                if info['tmdb_url']:
                    st.markdown(
                        f"[View ↗]({info['tmdb_url']})"
                    )
            st.markdown(
                "<hr style='border-color:#222;margin:8px 0'>",
                unsafe_allow_html=True
            )

    with c2:
        st.markdown("""
        <div style='background:#1a1a2a;border-radius:10px;
                    padding:16px;border:1px solid #3a3a6a;
                    margin-bottom:16px'>
            <div style='color:#7b68ee;font-size:12px;
                        text-transform:uppercase;
                        letter-spacing:1px'>System 2</div>
            <div style='color:#fff;font-size:18px;
                        font-weight:700'>Quantum</div>
            <div style='color:#7b68ee;font-size:12px'>
                IBM Kingston · 5 qubits · P@10: 0.0730
            </div>
        </div>
        """, unsafe_allow_html=True)

        quantum_recs = get_quantum_recs(
            models['ibm_features'],
            movies, history_ids, n=6
        )
        for _, row in quantum_recs.iterrows():
            info = get_movie_info(row['title'])
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                if info['poster_url']:
                    st.image(
                        info['poster_url'],
                        use_container_width=True
                    )
            with col_txt:
                st.markdown(
                    f"**{row['title'][:30]}**\n\n"
                    f"<span style='color:#888;font-size:11px'>"
                    f"{row['genres'].split('|')[0]}</span>",
                    unsafe_allow_html=True
                )
                if info['tmdb_url']:
                    st.markdown(
                        f"[View ↗]({info['tmdb_url']})"
                    )
            st.markdown(
                "<hr style='border-color:#222;margin:8px 0'>",
                unsafe_allow_html=True
            )

    with c3:
        st.markdown("""
        <div style='background:#1a0a0a;border-radius:10px;
                    padding:16px;border:1px solid #e50914;
                    margin-bottom:16px'>
            <div style='color:#e50914;font-size:12px;
                        text-transform:uppercase;
                        letter-spacing:1px'>
                System 3 — Best
            </div>
            <div style='color:#fff;font-size:18px;
                        font-weight:700'>
                Integrated Hybrid
            </div>
            <div style='color:#e50914;font-size:12px'>
                SVD + QPCA + TF-IDF · P@10: 0.1030
            </div>
        </div>
        """, unsafe_allow_html=True)

        integrated_recs = get_integrated_recs(
            genre_prefs,
            models['ibm_features'],
            models['qpca_features'],
            movies, models['tfidf_matrix'],
            history_ids, n=6
        )
        for _, row in integrated_recs.iterrows():
            info = get_movie_info(row['title'])
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                if info['poster_url']:
                    st.image(
                        info['poster_url'],
                        use_container_width=True
                    )
            with col_txt:
                st.markdown(
                    f"**{row['title'][:30]}**\n\n"
                    f"<span style='color:#888;font-size:11px'>"
                    f"{row['genres'].split('|')[0]}</span>",
                    unsafe_allow_html=True
                )
                if info['tmdb_url']:
                    st.markdown(
                        f"[View ↗]({info['tmdb_url']})"
                    )
            st.markdown(
                "<hr style='border-color:#222;margin:8px 0'>",
                unsafe_allow_html=True
            )


# ── WATCHLIST PAGE ────────────────────────────────────────────
elif page == "📋 My Watchlist":
    st.markdown(
        "<h2 style='color:#fff'>My Watchlist</h2>",
        unsafe_allow_html=True
    )

    watchlist = get_watchlist(username)

    if not watchlist:
        st.markdown("""
        <div style='text-align:center;padding:60px 0;
                    color:#555'>
            <div style='font-size:48px'>📋</div>
            <div style='font-size:18px;margin-top:12px'>
                Your watchlist is empty
            </div>
            <div style='font-size:14px;margin-top:8px'>
                Browse recommendations and click + List
                to save movies
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            f"<p style='color:#888'>"
            f"{len(watchlist)} movies saved</p>",
            unsafe_allow_html=True
        )
        cols = st.columns(5)
        for i, (movie_id, title, added_at) in enumerate(
            watchlist
        ):
            movie_row = movies[
                movies['movie_id'] == movie_id
            ]
            if not movie_row.empty:
                render_movie_card(
                    movie_row.iloc[0], cols[i % 5],
                    show_score=False
                )


# ── RESEARCH DASHBOARD ────────────────────────────────────────
elif page == "📊 Research Dashboard":
    st.markdown(
        "<h2 style='color:#fff'>Research Dashboard</h2>"
        "<p style='color:#888'>Experimental results and "
        "quantum hardware validation</p>",
        unsafe_allow_html=True
    )

    # IBM badge
    st.markdown("""
    <div class='ibm-badge' style='margin-bottom:24px'>
        ⚛️ <b>IBM Kingston Validated</b> · Job ID:
        d72htfuv3u3c73eimhn0 · 156-qubit Heron r2 ·
        Executed in 2 seconds · 1024 shots ·
        Mean noise deviation: 0.2238
    </div>
    """, unsafe_allow_html=True)

    # Three-way metrics
    st.markdown(
        "<div class='section-title'>"
        "Three-Way System Comparison</div>",
        unsafe_allow_html=True
    )

    r1, r2, r3 = st.columns(3)
    systems = [
        (r1, "System 1: Classical",
         "0.0715", "0.0287", "#564d44", "SVD only"),
        (r2, "System 2: Quantum IBM",
         "0.0730", "0.0291", "#7F77DD",
         "IBM Kingston hardware"),
        (r3, "System 3: Integrated ⭐",
         "0.1030", "0.0542", "#e50914",
         "SVD + QPCA + TF-IDF"),
    ]
    for col, name, p10, r10, color, sub in systems:
        with col:
            st.markdown(f"""
            <div style='background:#1a1a1a;
                        border:2px solid {color};
                        border-radius:12px;padding:20px;
                        text-align:center'>
                <div style='color:{color};font-weight:700;
                            font-size:14px;
                            text-transform:uppercase;
                            letter-spacing:1px'>
                    {name}
                </div>
                <div style='color:#888;font-size:12px;
                            margin:4px 0 16px'>{sub}</div>
                <div style='color:#fff;font-size:32px;
                            font-weight:700'>{p10}</div>
                <div style='color:#888;font-size:12px'>
                    Precision@10
                </div>
                <div style='color:#fff;font-size:24px;
                            font-weight:700;
                            margin-top:12px'>{r10}</div>
                <div style='color:#888;font-size:12px'>
                    Recall@10
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Improvement stats
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-title'>"
        "Integrated Hybrid Improvements</div>",
        unsafe_allow_html=True
    )

    i1, i2, i3, i4 = st.columns(4)
    improvements = [
        (i1, "P@10 vs Classical", "+44.1%", "#e50914"),
        (i2, "R@10 vs Classical", "+89.1%", "#e50914"),
        (i3, "P@10 vs Quantum",   "+41.1%", "#7F77DD"),
        (i4, "R@10 vs Quantum",   "+86.4%", "#7F77DD"),
    ]
    for col, label, val, color in improvements:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='color:#888;font-size:11px;
                            text-transform:uppercase'>
                    {label}
                </div>
                <div style='color:{color};font-size:32px;
                            font-weight:700'>{val}</div>
            </div>
            """, unsafe_allow_html=True)

    # Dissertation figure
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-title'>"
        "Dissertation Results Figure</div>",
        unsafe_allow_html=True
    )

    import os
    fig_path = "data/dissertation_final_figure.png"
    if os.path.exists(fig_path):
        st.image(fig_path, use_container_width=True)

    # Key findings
    st.markdown(
        "<div class='section-title'>Key Findings</div>",
        unsafe_allow_html=True
    )

    findings = [
        ("🔬", "Encoding Discovery",
         "Angle encoding preserves 0.0000 information loss "
         "vs amplitude at 0.5109 on sparse recommendation "
         "data — first systematic study for RecSys data"),
        ("⚛️", "QPCA Training",
         "40.7% training improvement on 32×32 user-item "
         "slice using 5-qubit variational quantum circuit "
         "with 3 entanglement layers"),
        ("🖥️", "Real Hardware Validation",
         "Circuit executed on IBM Kingston (156-qubit "
         "Heron r2) in 2 seconds. Recommendation rankings "
         "preserved despite 0.2238 mean noise deviation"),
        ("🏆", "Integration Result",
         "Integrated hybrid outperforms classical by "
         "+44.1% P@10 and +89.1% R@10. Proves quantum "
         "augmentation improves recommendation quality"),
    ]

    for icon, title, desc in findings:
        st.markdown(f"""
        <div style='background:#1a1a1a;border-radius:10px;
                    padding:16px;margin-bottom:12px;
                    border-left:4px solid #e50914'>
            <div style='font-size:20px;
                        display:inline'>{icon}</div>
            <span style='color:#fff;font-weight:700;
                         font-size:15px;
                         margin-left:8px'>{title}</span>
            <p style='color:#888;font-size:13px;
                      margin:8px 0 0'>{desc}</p>
        </div>
        """, unsafe_allow_html=True)