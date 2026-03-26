import streamlit as st
import pandas as pd
import cv2
import numpy as np
import qrcode
import smtplib
from email.message import EmailMessage
from datetime import datetime
import time
from io import BytesIO

# --- 1. CONFIGURATION (VERIFIE TES GID SUR GOOGLE SHEETS) ---
ID_SHEET = "1ROnvyK-h9I8mzAsfGjSRiQz8HLf5MppGVMCMt_vpiuM"
GID_ELEVES = "0" 
# Remplace les chiffres ci-dessous par ceux de ton navigateur (ex: gid=12345)
GID_PRESENCES = "1157441981" 
GID_RESULTATS = "408627258"

URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv"
URL_ELEVES = f"{URL_BASE}&gid={GID_ELEVES}"

st.set_page_config(page_title="EduTracer UPL 2026", page_icon="🎓", layout="wide")

# --- 2. STYLE VISUEL (POUR EVITER L'ECRAN NOIR) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #007bff; color: white; font-weight: bold; }
    .stDataFrame { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FONCTION EMAIL (AVEC TON NOUVEAU CODE : ncjzdgdxnplcptjj) ---
def envoyer_notification(email_dest, sujet, corps):
    try:
        msg = EmailMessage()
        msg.set_content(corps)
        msg['Subject'] = sujet
        msg['From'] = "julienbanze.k@gmail.com"
        msg['To'] = email_dest
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            # Utilisation du nouveau code généré aujourd'hui
            smtp.login("julienbanze.k@gmail.com", "ncjzdgdxnplcptjj") 
            smtp.send_message(msg)
        return True, "Envoyé"
    except Exception as e:
        return False, str(e)

# --- 4. CHARGEMENT SECURISE DES DONNEES ---
@st.cache_data(ttl=60)
def charger_donnees(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        # Création de l'identité selon tes titres exacts
        data['Identite'] = data['Nom_Eleve'].fillna('') + " " + data['Postnom_Eleve'].fillna('') + " " + data['Prenom_Eleve'].fillna('')
        return data
    except Exception as e:
        st.error(f"Erreur de connexion Google Sheets : {e}")
        return None

df_eleves = charger_donnees(URL_ELEVES)

# --- 5. NAVIGATION ADMIN ---
params = st.query_params
mode_admin = params.get("admin") == "upl"

if mode_admin:
    st.sidebar.title("🛠️ PANEL ADMIN UPL")
    menu = st.sidebar.selectbox("MENU :", ["Pointage Élèves", "Générer Cartes QR", "Tableau de Bord", "Calcul Bulletin"])
else:
    menu = "Pointage Élèves"

# --- 6. LOGIQUE DES PAGES ---

if df_eleves is None or df_eleves.empty:
    st.warning("⚠️ Chargement des données... Vérifiez le partage du fichier Google Sheets.")
else:
    # --- PAGE : POINTAGE ---
    if menu == "Pointage Élèves":
        st.title("🚀 Système de Présence & Alertes")
        
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            methode = st.radio("Méthode :", ["👤 Présence (Visage)", "💳 Carte Élève (QR)"], horizontal=True)
            photo = st.camera_input("Scanner l'étudiant")
            
        with col2:
            st.subheader("Validation")
            mat_input = st.text_input("🔢 Saisir le Matricule :", placeholder="Ex: 2025...")
            
            if st.button("VALIDER L'ARRIVÉE"):
                res = df_eleves[df_eleves['Matricule'].astype(str) == str(mat_input)]
                if not res.empty:
                    eleve = res.iloc[0]
                    with st.spinner('Envoi de l\'alerte au parent...'):
                        heure = datetime.now().strftime("%H:%M")
                        txt = f"UPL : L'étudiant {eleve['Identite']} est arrivé à l'université à {heure}."
                        ok, err = envoyer_notification(eleve['Email_Parent'], "🔔 Alerte Présence", txt)
                        
                        if ok:
                            st.success(f"✅ BIENVENU(E) {eleve['Identite']}")
                            st.info(f"📧 Notification envoyée à : {eleve['Email_Parent']}")
                            time.sleep(3)
                            st.rerun()
                        else:
                            st.error(f"❌ Erreur Email : {err}")
                else:
                    st.error("⚠️ Matricule inconnu dans la base de données.")

    # --- PAGE : GENERER CARTES ---
    elif menu == "Générer Cartes QR":
        st.title("🪪 Générateur de Cartes QR")
        sel = st.selectbox("Choisir l'élève :", df_eleves['Identite'].tolist())
        row = df_eleves[df_eleves['Identite'] == sel].iloc[0]
        
        qr = qrcode.make(str(row['Matricule']))
        st.image(qr.get_image(), width=200, caption=f"QR de {row['Matricule']}")
        st.info(f"**Identité :** {row['Identite']}\n\n**Matricule :** {row['Matricule']}")

    # --- PAGE : TABLEAU DE BORD (FIXÉ) ---
    elif menu == "Tableau de Bord":
        st.title("📋 Base de Données Étudiants")
        st.write(f"Nombre d'élèves enregistrés : {len(df_eleves)}")
        # Utilisation de st.dataframe pour un affichage propre et blanc
        st.dataframe(df_eleves[['Matricule', 'Nom_Eleve', 'Postnom_Eleve', 'Prenom_Eleve', 'Classe', 'Email_Parent']], use_container_width=True)

    # --- PAGE : CALCUL BULLETIN (FIXÉ) ---
    elif menu == "Calcul Bulletin":
        st.title("📊 Calculateur de Résultats Automatique")
        sel_b = st.selectbox("Élève pour le bulletin :", df_eleves['Identite'].tolist())
        info_b = df_eleves[df_eleves['Identite'] == sel_b].iloc[0]
        
        with st.form("form_res"):
            c1, c2 = st.columns(2)
            m = c1.number_input("Mathématiques /20", 0, 20, 10)
            c = c2.number_input("Autre Cours /20", 0, 20, 10)
            cond = c1.number_input("Conduite /10", 0, 10, 5)
            
            if st.form_submit_button("CALCULER & ENVOYER"):
                total = m + c + cond
                pourcent = (total / 50) * 100
                st.metric("RÉSULTAT", f"{pourcent}%", f"{total}/50")
                
                corps = f"Résultats UPL de {sel_b} :\nTotal: {total}/50\nPourcentage: {pourcent}%"
                ok, err = envoyer_notification(info_b['Email_Parent'], "📊 Bulletin Numérique", corps)
                if ok: st.success("✅ Bulletin envoyé au parent !")
                else: st.error(f"❌ Erreur : {err}")
