import streamlit as st

def login():
    st.title("🔐 Connexion")

    username = st.text_input("Nom utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if username and password:
            st.session_state.user = username
            st.rerun()
        else:
            st.error("Veuillez remplir tous les champs")

def logout():
    st.session_state.user = None
    st.rerun()