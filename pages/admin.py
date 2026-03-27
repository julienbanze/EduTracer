import streamlit as st
from database.supabase import supabase
from datetime import datetime

# =====================
# SECURITE ADMIN
# =====================
if not st.session_state.get("admin"):
    st.error("Accès refusé")
    st.stop()

st.title("👑 Administration École")

# =====================
# DATE HEURE SYSTEME
# =====================
now = datetime.now()

st.subheader("📅 Informations Système")

st.write("Date :", now.date())
st.write("Heure :", now.strftime("%H:%M:%S"))
st.write("Jour :", now.strftime("%A"))
st.write("Année :", now.year)

st.divider()

# =====================
# PARAMETRES ECOLE
# =====================
st.subheader("🏫 Paramètres École")

school_name = st.text_input("Nom de l'école")
academic_year = st.text_input("Année académique")
timezone = st.text_input("Fuseau horaire")

if st.button("Sauvegarder"):
    supabase.table("school_settings").insert({
        "school_name": school_name,
        "academic_year": academic_year,
        "timezone": timezone
    }).execute()

    st.success("Informations enregistrées")