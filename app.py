import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
from io import BytesIO

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="EduTracer UPL Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #eee; border-radius: 4px; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# Initialisation des bases de données en mémoire (Session)
if 'db_presences' not in st.session_state: st.session_state.db_presences = []
if 'db_resultats' not in st.session_state: st.session_state.db_resultats = []

# --- NAVIGATION ---
st.sidebar.title("💎 EDU-TRACER UPL")
role = st.sidebar.selectbox("Accès plateforme :", ["👨‍🎓 Borne de Pointage (Élève)", "⚙️ Panel Administration"])

# ---------------------------------------------------------
# 1. INTERFACE DE POINTAGE (ÉLÈVE)
# ---------------------------------------------------------
if role == "👨‍🎓 Borne de Pointage (Élève)":
    st.title("📲 Système de Pointage Biométrique / QR")
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        st.info("Utilisez la caméra pour le scan facial ou le code QR")
        st.camera_input("Scanner")
        
    with c2:
        st.subheader("Validation Manuelle")
        mat = st.text_input("🔢 Entrez votre Matricule :")
        if st.button("VALIDER L'ARRIVÉE", use_container_width=True):
            now = datetime.now()
            # Simulation d'enregistrement
            st.session_state.db_presences.append({
                "Matricule": mat, "Date": now.strftime("%d/%m/%Y"), 
                "Heure": now.strftime("%H:%M"), "Statut": "Présent"
            })
            st.success(f"✅ Identifié ! Bienvenue à l'UPL.")

# ---------------------------------------------------------
# 2. PANEL ADMINISTRATION
# ---------------------------------------------------------
else:
    st.title("⚙️ Gestion Administrative & Académique")
    t1, t2, t3 = st.tabs(["🪪 Création de Cartes", "📊 Encodage Résultats", "📈 Suivi Global"])

    # --- TAB 1 : CRÉATION DE CARTES ---
    with t1:
        st.subheader("🛠️ Générateur de Cartes Étudiant")
        with st.form("new_card"):
            c1, c2 = st.columns(2)
            m = c1.text_input("Matricule")
            n = c2.text_input("Nom")
            pn = c1.text_input("Postnom")
            pr = c2.text_input("Prénom")
            cl = st.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA", "L1 INFO"])
            
            if st.form_submit_button("Générer la Carte & QR"):
                # Génération QR
                data_qr = f"UPL-{m}-{n}"
                qr = qrcode.make(data_qr)
                buf = BytesIO()
                qr.save(buf, format="PNG")
                
                st.divider()
                col_a, col_b = st.columns([1, 2])
                col_a.image(buf, width=150)
                col_b.write(f"**CARTE GÉNÉRÉE**\n\n**Étudiant :** {n} {pn} {pr}\n\n**Matricule :** {m}\n\n**Classe :** {cl}")

    # --- TAB 2 : RÉSULTATS (COURS INTÉGRÉ) ---
    with t2:
        st.subheader("📊 Saisie des Notes par Cours")
        with st.form("form_notes"):
            c1, c2 = st.columns(2)
            mat_res = c1.text_input("Matricule de l'élève")
            nom_cours = c2.text_input("Nom du Cours (ex: Algorithmique)")
            
            c3, c4 = st.columns(2)
            note = c3.number_input("Note obtenue", 0.0, 100.0, 10.0)
            max_note = c4.number_input("Sur combien (Max)", 10, 100, 20)
            
            if st.form_submit_button("Calculer & Enregistrer le Bulletin"):
                pourcent = (note / max_note) * 100
                # Stockage dans l'onglet Résultats
                st.session_state.db_resultats.append({
                    "Matricule": mat_res,
                    "Cours": nom_cours,
                    "Cote": note,
                    "Total": max_note,
                    "Pourcentage": f"{pourcent}%"
                })
                st.success(f"✅ Résultat enregistré : {pourcent}% en {nom_cours}")

    # --- TAB 3 : SUIVI GLOBAL (PAR CLASSE) ---
    with t3:
        st.subheader("📈 Visualisation des Données")
        classe_view = st.selectbox("Sélectionner la classe à auditer :", ["Bac 1 IA", "Bac 2 IA"])
        
        col_p, col_r = st.columns(2)
        with col_p:
            st.write("📖 **Registre des Présences**")
            if st.session_state.db_presences:
                st.dataframe(pd.DataFrame(st.session_state.db_presences))
            else: st.info("Aucun scan aujourd'hui.")
            
        with col_r:
            st.write("📊 **Registre des Résultats**")
            if st.session_state.db_resultats:
                st.dataframe(pd.DataFrame(st.session_state.db_resultats))
            else: st.info("Aucune note encodée.")
