import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import time

# --- CONFIGURATION LUBUMBASHI (UTC+2) ---
st.set_page_config(page_title="EduTracer UPL - Biométrie Mobile", layout="wide", page_icon="📱")

def get_upl_time():
    return datetime.utcnow() + timedelta(hours=2)

# --- INITIALISATION DES BASES DE DONNÉES ---
DB_E = "base_etudiants.csv"
DB_P = "registre_empreintes.csv"

def init_db():
    if not os.path.exists(DB_E):
        pd.DataFrame([
            {"Matricule": "2025001", "Nom": "BANZE", "Postnom": "KANDOLO", "Prenom": "Julien", "Classe": "Bac 1 IA"},
            {"Matricule": "2025002", "Nom": "KABAMBA", "Postnom": "ILUNGA", "Prenom": "Marc", "Classe": "Bac 1 IA"}
        ]).to_csv(DB_E, index=False)
    if not os.path.exists(DB_P):
        pd.DataFrame(columns=["Matricule", "Date", "Pointage_1", "Pointage_2", "Statut"]).to_csv(DB_P, index=False)

init_db()

# --- DESIGN INDUSTRIEL DARK & MOBILE FRIENDLY ---
st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    .stButton>button { 
        background: linear-gradient(90deg, #238636 0%, #2ea043 100%); 
        color: white; border: none; border-radius: 12px; 
        width: 100%; font-weight: bold; height: 3.5em;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(46, 160, 67, 0.4); }
    .metric-card { 
        background: #161B22; border: 1px solid #30363D; 
        padding: 20px; border-radius: 15px; text-align: center;
    }
    .fingerprint-anim {
        text-align: center; padding: 20px; border: 2px dashed #58A6FF;
        border-radius: 50%; width: 150px; height: 150px; margin: auto;
    }
    h1, h2, h3 { color: #58A6FF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
st.sidebar.markdown("<h1 style='text-align: center;'>🛡️ EduTracer</h1>", unsafe_allow_html=True)
role = st.sidebar.radio("SÉLECTIONNER ESPACE :", ["🎓 Portail Étudiant (Mobile)", "🔐 Administration Centrale"])

# ---------------------------------------------------------
# 1. ESPACE ÉTUDIANT (Optimisé pour Empreinte Smartphone)
# ---------------------------------------------------------
if role == "🎓 Portail Étudiant (Mobile)":
    nav = st.sidebar.selectbox("SERVICES", ["☝️ Scanner Biométrique", "📊 Mes Résultats", "🗓️ Mon Historique"])

    if nav == "☝️ Scanner Biométrique":
        st.title("☝️ Authentification Biométrique")
        st.write("Utilisez le capteur d'empreinte de votre appareil pour pointer.")
        
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.markdown("<br>", unsafe_allow_html=True)
            st.image("https://img.icons8.com/ios/150/58A6FF/fingerprint.png")
            mat_in = st.text_input("Numéro Matricule", placeholder="Ex: 2025001").strip()
        
        with c2:
            st.write("### État du Capteur")
            if st.button("ACTIVER LE SCANNER (EMPREINTE)"):
                if mat_in:
                    df_e = pd.read_csv(DB_E)
                    if mat_in in df_e['Matricule'].astype(str).values:
                        with st.spinner("Vérification biométrique sur l'appareil..."):
                            time.sleep(1.5) # Simulation du temps de scan sur téléphone
                            
                            df_p = pd.read_csv(DB_P)
                            today = get_upl_time().strftime("%d/%m/%Y")
                            now_time = get_upl_time().strftime("%H:%M")
                            
                            # Logique de double pointage
                            row_idx = df_p[(df_p['Matricule'] == mat_in) & (df_p['Date'] == today)].index
                            
                            if len(row_idx) == 0:
                                # Premier passage (Entrée)
                                new_log = pd.DataFrame([{"Matricule": mat_in, "Date": today, "Pointage_1": now_time, "Pointage_2": None, "Statut": "Partiel"}])
                                pd.concat([df_p, new_log]).to_csv(DB_P, index=False)
                                st.success(f"✅ POINTAGE ENTRÉE RÉUSSI ({now_time})")
                                st.toast("Données synchronisées avec le serveur UPL", icon='☁️')
                            else:
                                # Deuxième passage (Sortie)
                                if pd.isna(df_p.loc[row_idx[0], 'Pointage_2']):
                                    df_p.loc[row_idx[0], 'Pointage_2'] = now_time
                                    df_p.loc[row_idx[0], 'Statut'] = "Présent"
                                    df_p.to_csv(DB_P, index=False)
                                    st.success(f"✅ POINTAGE SORTIE RÉUSSI ({now_time})")
                                    st.balloons()
                                else:
                                    st.warning("⚠️ Présence déjà complète pour aujourd'hui.")
                    else:
                        st.error("❌ Matricule non reconnu dans la base.")
                else:
                    st.warning("Veuillez saisir votre matricule avant de scanner.")

    elif nav == "📊 Mes Résultats":
        st.title("📊 Calculateur de Performance")
        with st.container():
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            nb = st.number_input("Nombre de matières", 1, 15, 5)
            notes = [st.number_input(f"Note /20 - Cours {i+1}", 0, 20, 10, key=i) for i in range(nb)]
            if st.button("GÉNÉRER MON BULLETIN"):
                moy = (sum(notes) / (nb * 20)) * 100
                st.write(f"## Votre Pourcentage : {round(moy, 2)}%")
                if moy >= 50: st.success("Félicitations ! Vous avez réussi.")
                else: st.error("Travaillez encore, vous êtes en dessous de 50%.")
            st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. ESPACE ADMINISTRATION (Gestion Totale)
# ---------------------------------------------------------
else:
    st.title("🔐 Administration Centrale EduTracer")
    
    # Statistiques Globales
    df_p = pd.read_csv(DB_P)
    df_e = pd.read_csv(DB_E)
    today = get_upl_time().strftime("%d/%m/%Y")
    presences_today = df_p[df_p['Date'] == today]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f"<div class='metric-card'><h5>Total Inscrits</h5><h2>{len(df_e)}</h2></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-card'><h5>Présents (Complets)</h5><h2>{len(presences_today[presences_today['Statut']=='Présent'])}</h2></div>", unsafe_allow_html=True)
    m3.markdown(f"<div class='metric-card'><h5>En cours (Entrée seule)</h5><h2>{len(presences_today[presences_today['Statut']=='Partiel'])}</h2></div>", unsafe_allow_html=True)
    absents = len(df_e) - len(presences_today)
    m4.markdown(f"<div class='metric-card'><h5>Absents</h5><h2>{absents}</h2></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Registre Global", "👥 Gestion Étudiants", "📊 Analyses IA"])
    
    with tab1:
        st.subheader("Fichier des Présences Journalières")
        st.dataframe(df_p.sort_values(by=["Date", "Pointage_1"], ascending=False), use_container_width=True)
        st.download_button("📥 Exporter le registre pour le Secrétariat", df_p.to_csv(index=False), "Rapport_UPL.csv")

    with tab2:
        st.subheader("Mise à jour de la Base de Données")
        with st.expander("➕ Ajouter un nouvel étudiant"):
            with st.form("new_st"):
                c1, c2, c3 = st.columns(3)
                m = c1.text_input("Matricule")
                n = c2.text_input("Nom & Postnom")
                p = c3.text_input("Prénom")
                cl = st.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA", "L1 INFO", "L2 INFO"])
                if st.form_submit_button("VALIDER INSCRIPTION"):
                    if m and n:
                        df_e = pd.read_csv(DB_E)
                        new_row = pd.DataFrame([{"Matricule": m, "Nom": n.upper(), "Postnom": "", "Prenom": p, "Classe": cl}])
                        pd.concat([df_e, new_row]).to_csv(DB_E, index=False)
                        st.success("Étudiant ajouté avec succès !")
                        st.rerun()
        
        st.dataframe(df_e, use_container_width=True)

    with tab3:
        st.subheader("Visualisation des données d'assiduité")
        if not df_p.empty:
            st.bar_chart(df_p['Classe'].value_counts())
        else:
            st.info("Aucune donnée d'analyse disponible pour le moment.")
