import streamlit as st
from database.supabase import supabase

st.title("📝 Notes")

students = supabase.table("students").select("*").execute()

student_dict = {s["name"]: s["id"] for s in students.data}

student = st.selectbox("Étudiant", student_dict.keys())
course = st.text_input("Cours")
grade = st.number_input("Note", 0, 100)

if st.button("Enregistrer"):
    supabase.table("grades").insert({
        "student_id": student_dict[student],
        "course": course,
        "grade": grade
    }).execute()

    st.success("Note enregistrée")