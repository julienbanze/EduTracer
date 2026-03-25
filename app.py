import streamlit as st
import pandas as pd
import cv2
import numpy as np
import qrcode
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- 1. CONFIGURATION DES URLS (BASÉE SUR TES ONGLETS) ---
ID_SHEET = "1ROnvyK-h9I8mzAsfGjSRiQz8HLf5MppGVMCMt_vpiuM"

# ⚠️ REMPLACE CES GID PAR LES CHIFFRES APRÈS gid= DANS TON NAVIGATEUR
GID_ELEVES = "0" 
GID_PRESENCES = "1157441981" 
GID_RESULTATS = "408627258"

URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv"
URL_ELEVES = f"{URL_BASE}&gid={GID_ELEVES}"

st.set_page_config(page_title="EduTracer UPL", page_icon="🎓", layout="wide")

# --- 2. FONCTION EMAIL (Code: ncdjibbdcydgyqhu) ---
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
    except: return False

# --- 3. CHARGEMENT DES DONNÉES ---
@st.cache_data
def charger_donnees(url):
    try:
        data = pd.read_csv(url)
        # Nettoyage automatique des noms de colonnes (enlève les espaces invisibles)
        data.columns = data.columns.str.strip()
        # Création de l'identité complète selon tes titres
        data['Identite'] = data['Nom_Eleve'].astype(str) + " " + data['Postnom_Eleve'].astype(str) + " " + data['Prenom_Eleve'].astype(str)
        return data
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        return None

df_eleves = charger_donnees(URL_ELEVES)

# --- 4. LOGIQUE ADMIN INVISIBLE ---
params = st.query_params
mode_admin = params.get("admin") == "upl"

# --- 5. INTERFACE ---
if mode_admin:
    st.sidebar.title("👨‍✈️ Administration UPL")
    menu = st.sidebar.radio("Navigation", ["Pointage Élèves", "Générer Cartes QR", "Tableau de Bord", "Calcul Bulletin"])
else:
    menu = "Pointage Élèves"

# --- LOGIQUE DES PAGES ---
if df_eleves is not None:
    if menu == "Pointage Élèves":
        st.title(" Système de Présence")
        choix = st.radio("Méthode :", ["👤 Présence (Visage)", "💳 Carte Élève (QR)"], horizontal=True)
        st.camera_input("Scanner")
        mat_input = st.text_input("Saisir Matricule :")
        if st.button("Valider l'Arrivée"):
            res = df_eleves[df_eleves['Matricule'].astype(str) == str(mat_input)]
            if not res.empty:
                eleve = res.iloc[0]
                st.success(f"✅ BIENVENU(E) : {eleve['Identite']}")
                envoyer_notification(eleve['Email_Parent'], "🔔 Arrivée UPL", f"L'étudiant {eleve['Identite']} est bien arrivé.")
            else: st.error("Matricule inconnu.")

    elif menu == "Générer Cartes QR":
        st.title("🪪 Générateur de Cartes QR")
        nom_sel = st.selectbox("Choisir l'étudiant :", df_eleves['Identite'].tolist())
        infos = df_eleves[df_eleves['Identite'] == nom_sel].iloc[0]
        qr = qrcode.make(str(infos['Matricule']))
        st.image(qr.get_image(), caption=f"QR de {infos['Matricule']}", width=200)
        st.write(f"**Identité :** {infos['Identite']}")
        st.write(f"**Matricule :** {infos['Matricule']}")

    elif menu == "Tableau de Bord":
        st.title("📋 Base de Données")
        st.dataframe(df_eleves)

    elif menu == "Calcul Bulletin":
        st.title("📊 Calculateur Automatique de Pourcentage")
        nom_sel = st.selectbox("Sélectionner l'étudiant :", df_eleves['Identite'].tolist())
        eleve_n = df_eleves[df_eleves['Identite'] == nom_sel].iloc[0]
        
        with st.form("form_notes"):
            col1, col2 = st.columns(2)
            with col1:
                math = st.number_input("Note Math (sur 20)", 0, 20)
                cours = st.number_input("Note Autre Cours (sur 20)", 0, 20)
            with col2:
                cote = st.number_input("Note Cote (sur 10)", 0, 10)
            
            if st.form_submit_button("Calculer et Envoyer"):
                # Calcul automatique
                total_obtenu = math + cours + cote
                total_max = 50 # (20 + 20 + 10)
                pourcentage = (total_obtenu / total_max) * 100
                
                st.success(f"Calcul terminé ! Total : {total_obtenu}/{total_max} | Pourcentage : {pourcentage:.2f}%")
                
                # Envoi du mail au parent
                corps_mail = f"Résultats de {nom_sel} :\nMath: {math}/20\nCours: {cours}/20\nCote: {cote}/10\nTotal: {total_obtenu}/50\nPourcentage: {pourcentage:.2f}%"
                envoyer_notification(eleve_n['Email_Parent'], "📊 Bulletin Numérique", corps_mail)
                st.info("E-mail envoyé avec succès.")