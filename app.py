import streamlit as st
from utils.auth import login, logout

st.set_page_config(
    page_title="Plateforme Scolaire",
    layout="wide"
)

# =========================
# DETECTION ADMIN
# =========================
params = st.query_params

if params.get("admin") == "julien":
    st.session_state.admin = True
else:
    st.session_state.admin = False

# =========================
# SESSION USER
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

# =========================
# LOGIN
# =========================
if not st.session_state.user:
    login()
else:

    st.sidebar.success(f"Connecté : {st.session_state.user}")

    if st.session_state.admin:
        st.sidebar.success("👑 MODE ADMIN ACTIVÉ")

    if st.sidebar.button("Déconnexion"):
        logout()

    st.title("🎓 Plateforme de Gestion Scolaire")
    st.write("Bienvenue dans le système.")
