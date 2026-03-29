import requests
import streamlit as st

TMDB_KEY     = "fe62152d82255c8c555b5f146a9a0331"
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w500"
TMDB_SEARCH  = f"{TMDB_BASE}/search/movie"
TMDB_DETAIL  = f"{TMDB_BASE}/movie"


@st.cache_data(ttl=3600)
def search_movie_tmdb(title, year=None):
    """Search TMDB for a movie by title."""
    try:
        query  = title.split('(')[0].strip()
        params = {
            'api_key': TMDB_KEY,
            'query'  : query,
            'language': 'en-US',
            'page'   : 1
        }
        if year:
            params['year'] = year

        resp = requests.get(
            TMDB_SEARCH, params=params, timeout=5
        )
        data = resp.json()

        if data.get('results'):
            return data['results'][0]
        return None

    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_movie_details(tmdb_id):
    """Get full movie details from TMDB."""
    try:
        params = {
            'api_key'            : TMDB_KEY,
            'language'           : 'en-US',
            'append_to_response' : 'videos,credits'
        }
        resp = requests.get(
            f"{TMDB_DETAIL}/{tmdb_id}",
            params=params, timeout=5
        )
        return resp.json()
    except Exception:
        return None


def get_poster_url(poster_path):
    """Get full poster URL."""
    if poster_path:
        return f"{TMDB_IMG}{poster_path}"
    return None


def get_tmdb_page_url(tmdb_id):
    """Get TMDB movie page URL."""
    return f"https://www.themoviedb.org/movie/{tmdb_id}"


@st.cache_data(ttl=3600)
def get_movie_info(title):
    """
    Get movie poster URL and TMDB link.
    Returns dict with poster_url and tmdb_url.
    """
    result = search_movie_tmdb(title)

    if result:
        poster_url = get_poster_url(
            result.get('poster_path')
        )
        tmdb_url   = get_tmdb_page_url(result['id'])
        return {
            'tmdb_id'    : result['id'],
            'poster_url' : poster_url,
            'tmdb_url'   : tmdb_url,
            'overview'   : result.get('overview', ''),
            'rating'     : result.get('vote_average', 0),
            'release'    : result.get('release_date', ''),
            'title'      : result.get('title', title)
        }

    return {
        'tmdb_id'    : None,
        'poster_url' : None,
        'tmdb_url'   : None,
        'overview'   : '',
        'rating'     : 0,
        'release'    : '',
        'title'      : title
    }