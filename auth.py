import streamlit as st
from database import (
    register_user, login_user,
    save_genre_prefs, init_db
)

GENRES = [
    "Action", "Adventure", "Animation",
    "Children", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy",
    "Film-Noir", "Horror", "Musical",
    "Mystery", "Romance", "Sci-Fi",
    "Thriller", "War", "Western"
]


def show_login_page():
    """Render the login page."""

    st.markdown("""
    <div style='text-align:center; padding: 40px 0 20px'>
        <h1 style='color:#e50914; font-size:48px;
                   font-weight:900; letter-spacing:4px;
                   margin-bottom:4px'>
            QUANTUMREC
        </h1>
        <p style='color:#888; font-size:14px;
                  letter-spacing:2px'>
            HYBRID QUANTUM-CLASSICAL MOVIE RECOMMENDER
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("""
        <div style='background:#1a1a1a; padding:32px;
                    border-radius:12px;
                    border:1px solid #333'>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Sign In", "Register"])

        with tab1:
            _login_form()

        with tab2:
            _register_form()

        st.markdown("</div>", unsafe_allow_html=True)


def _login_form():
    """Login form."""
    st.markdown(
        "<h3 style='color:#fff; margin-bottom:20px'>"
        "Welcome back</h3>",
        unsafe_allow_html=True
    )

    username = st.text_input(
        "Username",
        placeholder="Enter your username",
        key="login_username"
    )
    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        key="login_password"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "Sign In", use_container_width=True,
        type="primary"
    ):
        if not username or not password:
            st.error("Please fill in all fields")
            return

        success, user_data = login_user(username, password)

        if success:
            st.session_state.logged_in   = True
            st.session_state.user        = user_data
            st.session_state.username    = username
            st.session_state.is_new_user = user_data['is_new_user']
            st.success(f"Welcome back, {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password")


def _register_form():
    """Registration form."""
    st.markdown(
        "<h3 style='color:#fff; margin-bottom:20px'>"
        "Create account</h3>",
        unsafe_allow_html=True
    )

    username = st.text_input(
        "Username",
        placeholder="Choose a username",
        key="reg_username"
    )
    email = st.text_input(
        "Email",
        placeholder="Enter your email",
        key="reg_email"
    )
    password = st.text_input(
        "Password",
        type="password",
        placeholder="Create a password (min 6 chars)",
        key="reg_password"
    )
    confirm = st.text_input(
        "Confirm Password",
        type="password",
        placeholder="Repeat your password",
        key="reg_confirm"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "Create Account",
        use_container_width=True,
        type="primary"
    ):
        if not all([username, email, password, confirm]):
            st.error("Please fill in all fields")
            return
        if len(password) < 6:
            st.error("Password must be at least 6 characters")
            return
        if password != confirm:
            st.error("Passwords do not match")
            return
        if '@' not in email:
            st.error("Please enter a valid email")
            return

        success, msg = register_user(username, email, password)

        if success:
            st.success(
                "Account created! Please sign in."
            )
        else:
            st.error(msg)


def show_genre_selection():
    """First-time genre selection screen."""
    st.markdown("""
    <div style='text-align:center; padding:30px 0'>
        <h1 style='color:#e50914'>Welcome to QuantumRec</h1>
        <p style='color:#aaa; font-size:16px'>
            Select your favourite genres so we can
            personalise your recommendations
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "<p style='color:#888; text-align:center'>"
        "Choose at least 3 genres</p>",
        unsafe_allow_html=True
    )

    # Genre grid
    selected = []
    cols     = st.columns(6)

    for i, genre in enumerate(GENRES):
        with cols[i % 6]:
            if st.checkbox(genre, key=f"genre_{genre}"):
                selected.append(genre)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(
            "Start Exploring",
            use_container_width=True,
            type="primary",
            disabled=len(selected) < 3
        ):
            save_genre_prefs(
                st.session_state.username, selected
            )
            st.session_state.user['genre_prefs']  = selected
            st.session_state.user['is_new_user']  = 0
            st.session_state.is_new_user           = 0
            st.rerun()

    if len(selected) < 3:
        st.markdown(
            f"<p style='text-align:center; color:#888'>"
            f"Select {3-len(selected)} more genre(s) "
            f"to continue</p>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<p style='text-align:center; color:#e50914'>"
            f"{len(selected)} genres selected ✓</p>",
            unsafe_allow_html=True
        )