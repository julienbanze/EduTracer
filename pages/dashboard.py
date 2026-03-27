import streamlit as st
from database.supabase import supabase
from datetime import date

st.title("📊 Dashboard")

students = supabase.table("students").select("*").execute()
teachers = supabase.table("teachers").select("*").execute()
attendance = supabase.table("attendance").select("*").eq(
    "date", str(date.today())
).execute()

total_students = len(students.data) if students.data else 0
total_teachers = len(teachers.data) if teachers.data else 0
today_attendance = len(attendance.data) if attendance.data else 0

c1, c2, c3 = st.columns(3)

c1.metric("Étudiants", total_students)
c2.metric("Enseignants", total_teachers)
c3.metric("Présences Aujourd’hui", today_attendance)