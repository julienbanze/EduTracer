import streamlit as st
from database.supabase import supabase

st.title("👨‍🎓 Étudiants")

with st.form("student_form"):
    name = st.text_input("Nom")
    classe = st.text_input("Classe")
    submit = st.form_submit_button("Ajouter")

    if submit:
        supabase.table("students").insert({
            "name": name,
            "classe": classe
        }).execute()
        st.success("Étudiant ajouté")
        st.rerun()

data = supabase.table("students").select("*").execute()
st.dataframe(data.data)