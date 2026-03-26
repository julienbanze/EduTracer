import streamlit as st
import pandas as pd
import qrcode
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
import os

# --- CONFIGURATION & HEURE LOCALE LUBUMBASHI (UTC+2) ---
st.set_page_config(page_title="EduTracer UPL Pro", layout="wide", page_icon="🎓")

def get_rdc_time():
    # Lubumbashi est à UTC+2
    return datetime.utcnow() + timedelta(hours=2)

# --- GESTION DES FICHIERS DE DONNÉES (PERSISTENCE) ---
DB_ELEVES = "database_students.csv"
DB_LOGS = "attendance_logs.csv"

def init_db():
    if not os.path.exists(DB_ELEVES):
        pd.DataFrame(columns=["Matricule", "Nom", "Postnom", "Prenom", "Classe"]).to_csv(DB_ELEVES, index=False)
    if not os.path.exists(DB_LOGS):
        pd.DataFrame(columns=["Matricule", "Identite", "Classe", "Date", "Heure"]).to_csv(DB_LOGS, index=False)

init_db()

# --- DESIGN CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .main-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 6px solid #004e92; }
    .stButton>button { border-radius: 8px; font-weight: bold; height: 3em; transition: 0.3s; }
    .sidebar-text { color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- VÉRIFICATION ADMIN ---
is_admin = st.query_params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE ÉTUDIANT (PORTAIL PUBLIC)
# ---------------------------------------------------------
if not is_admin:
    st.sidebar.markdown("<h2 style='color:white;'>🎓 UPL Portal</h2>", unsafe_allow_html=True)
    nav = st.sidebar.radio("Menu principal :", ["📍 Présence Biométrique", "📊 Calcul Bulletin"])

    if nav == "📍 Présence Biométrique":
        st.markdown("<h2 style='color:#004e92;'>📸 Pointage Facial & Biométrique</h2>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.2])
        
        with c1:
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            st.camera_input("Scanner facial", label_visibility="collapsed")
            input_id = st.text_input("Veuillez entrer votre Matricule (Simulation scan)")
            if st.button("ENREGISTRER MA PRÉSENCE", use_container_width=True):
                df_e = pd.read_csv(DB_ELEVES)
                match = df_e[df_e['Matricule'].astype(str) == input_id]
                
                if not match.empty:
                    info = match.iloc[0]
                    nom_full = f"{info['Nom']} {info['Prenom']}"
                    t_rdc = get_rdc_time()
                    
                    # Sauvegarde dans le registre
                    df_l = pd.read_csv(DB_LOGS)
                    new_entry = pd.DataFrame([{
                        "Matricule": input_id, "Identite": nom_full, 
                        "Classe": info['Classe'], "Date": t_rdc.strftime("%d/%m/%Y"), 
                        "Heure": t_rdc.strftime("%H:%M:%S")
                    }])
                    pd.concat([df_l, new_entry]).to_csv(DB_LOGS, index=False)
                    
                    st.success(f"✅ Bonjour {nom_full}, votre présence est notée à {t_rdc.strftime('%H:%M')}")
                    st.balloons()
                else:
                    st.error("❌ Matricule non reconnu. Contactez la scolarité.")
            st.markdown("</div>", unsafe_allow_html=True)

    elif nav == "📊 Calcul Bulletin":
        st.markdown("<h2 style='color:#004e92;'>🧮 Calculateur de Moyenne</h2>", unsafe_allow_html=True)
        nb_m = st.number_input("Nombre de matières :", 1, 12, 5)
        with st.form("calc_form"):
            cols = st.columns(3)
            pts, total_max = [], []
            for i in range(int(nb_m)):
                with cols[i%3]:
                    pts.append(st.number_input(f"Note {i+1}", 0.0, 100.0, 10.0))
                    total_max.append(st.number_input(f"Sur (Max)", 1.0, 100.0, 20.0))
            if st.form_submit_button("CALCULER LE RÉSULTAT"):
                perc = (sum(pts)/sum(total_max)) * 100
                st.metric("POURCENTAGE", f"{round(perc, 2)}%")
                if perc >= 80: st.success("MENTION : EXCELLENT 🌟")
                elif perc >= 70: st.info("MENTION : DISTINCTION 🎓")
                elif perc >= 50: st.warning("MENTION : SATISFACTION ✅")
                else: st.error("MENTION : AJOURNÉ ❌")

# ---------------------------------------------------------
# INTERFACE ADMIN (GESTION & STATISTIQUES)
# ---------------------------------------------------------
else:
    st.markdown("<h1 style='color:#004e92;'>👑 Administration Centrale - Julien</h1>", unsafe_allow_html=True)
    
    # Navigation simplifiée pour l'admin
    onglet = st.radio("SÉLECTIONNER UNE ACTION :", 
                      ["📊 Statistiques & Logs", "👥 Gestion Scolarité", "🪪 Générateur QR"],
                      horizontal=True)
    
    st.divider()

    # 1. STATISTIQUES & LOGS
    if onglet == "📊 Statistiques & Logs":
        df_logs = pd.read_csv(DB_LOGS)
        
        if not df_logs.empty:
            c_stats, c_table = st.columns([1, 1.5])
            
            with c_stats:
                st.write("### Répartition par Classe")
                # Création du graphique Pie Chart (Camembert)
                classe_counts = df_logs['Classe'].value_counts()
                fig, ax = plt.subplots()
                ax.pie(classe_counts, labels=classe_counts.index, autopct='%1.1f%%', startangle=90, colors=['#004e92', '#28a745', '#ffc107', '#dc3545'])
                ax.axis('equal') 
                st.pyplot(fig)
            
            with c_table:
                st.write("### Journal des pointages (Lubumbashi)")
                st.dataframe(df_logs, use_container_width=True)
                st.download_button("📥 Exporter Registre (CSV)", df_logs.to_csv(index=False), "attendance_upl.csv")
        else:
            st.info("Aucune présence enregistrée aujourd'hui.")

    # 2. GESTION SCOLARITÉ (AJOUT ÉLÈVES)
    elif onglet == "👥 Gestion Scolarité":
        st.subheader("➕ Ajouter un nouvel étudiant à la base")
        with st.form("new_student"):
            c1, c2, c3 = st.columns(3)
            m = c1.text_input("Matricule Unique")
            n = c2.text_input("Nom")
            pn = c3.text_input("Postnom")
            pr = c1.text_input("Prénom")
            cl = c2.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA", "L1 INFO", "L2 INFO"])
            
            if st.form_submit_button("ENREGISTRER DANS LA BASE"):
                if m and n:
                    df_e = pd.read_csv(DB_ELEVES)
                    new_st = pd.DataFrame([{"Matricule": m, "Nom": n.upper(), "Postnom": pn.upper(), "Prenom": pr, "Classe": cl}])
                    pd.concat([df_e, new_st]).to_csv(DB_ELEVES, index=False)
                    st.success(f"Étudiant {n} enregistré avec succès !")
                else: st.error("Le matricule et le nom sont obligatoires.")
        
        st.divider()
        st.write("### Liste Globale des Inscrits")
        st.dataframe(pd.read_csv(DB_ELEVES), use_container_width=True)

    # 3. GÉNÉRATEUR QR
    elif onglet == "🪪 Générateur QR":
        st.subheader("Générer un QR Code de sécurité")
        id_qr = st.text_input("Matricule de l'élève pour le QR")
        if st.button("Générer le Code"):
            qr_code = qrcode.make(id_qr)
            b = BytesIO()
            qr_code.save(b, format="PNG")
            st.image(b, width=250, caption=f"ID: {id_qr}")

    # BOUTON RETOUR / DÉCONNEXION SIMULÉ
    if st.sidebar.button("🚪 Déconnexion Admin"):
        st.query_params.clear()
        st.rerun()
