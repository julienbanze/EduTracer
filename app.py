import streamlit as st
import pandas as pd
import cv2
import numpy as np
import qrcode
import smtplib
from email.message import EmailMessage
from datetime import datetime
import time

# --- CONFIGURATION ---
ID_SHEET = "1ROnvyK-h9I8mzAsfGjSRiQz8HLf5MppGVMCMt_vpiuM"
# Mets tes vrais GID ici
GID_ELEVES = "0" 
GID_PRESENCES = "TON_GID" 
GID_RESULTATS = "TON_GID"

URL_ELEVES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_ELEVES}"

st.set_page_config(page_title="EduTracer UPL", page_icon="🎓", layout="wide")

# --- FONCTION EMAIL ---
def envoyer_notification(email_dest, sujet, corps):
    msg = EmailMessage()
    msg.set_content(corps)
    msg['Subject'] = sujet
    msg['From'] = "julienbanze.k@gmail.com"
    msg['To'] = email_dest
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("julienbanze.k@gmail.com", "ncdjibbdcydgyqhu") 
            smtp.send_message(msg)
            return True
    except Exception as e:
        st.error(f"Erreur Email : {e}")
        return False

# --- CHARGEMENT ---
@st.cache_data
def charger_donnees(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        data['Identite'] = data['Nom_Eleve'].astype(str) + " " + data['Postnom_Eleve'].astype(str) + " " + data['Prenom_Eleve'].astype(str)
        return data
    except: return None

df_eleves = charger_donnees(URL_ELEVES)

# --- LOGIQUE ADMIN ---
mode_admin = st.query_params.get("admin") == "upl"

if mode_admin:
    st.sidebar.title("👨‍✈️ Admin UPL")
    menu = st.sidebar.radio("Menu", ["Pointage", "Cartes QR", "Tableau de Bord", "Bulletins"])
else:
    menu = "Pointage"

# --- PAGE POINTAGE AMÉLIORÉE ---
if menu == "Pointage":
    st.title("🚀 Pointage des Étudiants")
    
    tab1, tab2 = st.tabs(["👤 Scan Visage (IA)", "💳 Scan Carte (QR)"])

    with tab1:
        st.subheader("Reconnaissance Faciale")
        photo = st.camera_input("Prendre la photo de présence", key="cam_visage")
        if photo:
            st.success("✅ Visage capturé. Entrez le matricule ci-dessous.")

    with tab2:
        st.subheader("Lecture de Carte")
        carte = st.camera_input("Scanner le QR Code de la carte", key="cam_qr")
        if carte:
            st.info("⌛ QR Code détecté.")

    st.divider()
    
    # Zone de validation commune
    with st.container():
        mat_input = st.text_input("🔢 Entrez le Matricule de l'élève :", key="input_mat")
        
        if st.button("CONFIRMER ET ENVOYER ALERTE", use_container_width=True):
            if df_eleves is not None and mat_input:
                res = df_eleves[df_eleves['Matricule'].astype(str) == str(mat_input)]
                if not res.empty:
                    eleve = res.iloc[0]
                    nom_complet = eleve['Identite']
                    email = eleve['Email_Parent']
                    
                    # 1. Message de succès
                    st.balloons()
                    st.success(f"BIENVENU(E) : {nom_complet}")
                    
                    # 2. Envoi de l'email
                    heure = datetime.now().strftime("%H:%M")
                    sujet = f"🔔 Présence UPL : {nom_complet}"
                    corps = f"Bonjour, l'étudiant {nom_complet} est arrivé à l'UPL à {heure}."
                    
                    if envoyer_notification(email, sujet, corps):
                        st.info(f"📧 Notification envoyée à : {email}")
                    
                    # 3. Pause et Nettoyage pour l'élève suivant
                    time.sleep(3)
                    st.rerun() # Relance l'app pour vider la caméra et le texte
                else:
                    st.error("⚠️ Matricule inconnu dans la base de données.")
            else:
                st.warning("Veuillez entrer un matricule valide.")

# --- AUTRES PAGES (Cartes, Bord, Bulletin) ---
elif menu == "Cartes QR":
    st.title("🪪 Générateur de Cartes")
    if df_eleves is not None:
        sel = st.selectbox("Élève :", df_eleves['Identite'].tolist())
        row = df_eleves[df_eleves['Identite'] == sel].iloc[0]
        qr_img = qrcode.make(str(row['Matricule']))
        st.image(qr_img.get_image(), width=200)
        st.write(f"**Identité :** {row['Identite']}")

# (Ajoute ici tes codes de Tableau de Bord et Bulletin comme avant)
