import streamlit as st
from database.supabase import supabase

st.title("👩‍🏫 Enseignants")

with st.form("teacher_form"):
    name = st.text_input("Nom enseignant")
    course = st.text_input("Matière")
    submit = st.form_submit_button("Ajouter")

    if submit:
        supabase.table("teachers").insert({
            "name": name,
            "course": course
        }).execute()
        st.success("Enseignant ajouté")
        st.rerun()

data = supabase.table("teachers").select("*").execute()
st.dataframe(data.data)