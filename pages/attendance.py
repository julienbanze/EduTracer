import streamlit as st
from database.supabase import supabase
from datetime import date

st.title("✅ Présence")

students = supabase.table("students").select("*").execute()

student_names = {
    s["name"]: s["id"] for s in students.data
}

selected = st.selectbox("Choisir étudiant", list(student_names.keys()))

if st.button("Marquer Présent"):
    supabase.table("attendance").insert({
        "student_id": student_names[selected],
        "date": str(date.today())
    }).execute()

    st.success("Présence enregistrée")