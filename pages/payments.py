import streamlit as st
from database.supabase import supabase

st.title("💰 Paiements")

students = supabase.table("students").select("*").execute()
student_dict = {s["name"]: s["id"] for s in students.data}

student = st.selectbox("Étudiant", student_dict.keys())
amount = st.number_input("Montant")

if st.button("Valider paiement"):
    supabase.table("payments").insert({
        "student_id": student_dict[student],
        "amount": amount
    }).execute()

    st.success("Paiement enregistré")