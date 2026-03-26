import streamlit as st
import pandas as pd
import cv2
import numpy as np
import qrcode
import smtplib
from email.message import EmailMessage
from datetime import datetime
import time

# --- CONFIGURATION (VERIFIE BIEN TES GID) ---
ID_SHEET = "1ROnvyK-h9I8mzAsfGjSRiQz8HLf5MppGVMCMt_vpiuM"
GID_ELEVES = "0" 
GID_PRESENCES = "TON_GID_ICI" 
GID_RESULTATS = "TON_GID_ICI"

URL_ELEVES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_ELEVES}"

st.set_page_config(page_title="EduTracer UPL 2026", page_icon="🎓", layout="wide")

# --- STYLE CSS POUR EVITER LE NOIR ET RENDRE PROPRE ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stDataFrame { background-color: white; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION EMAIL (Code: ncdjibbdcydgyqhu) ---
def envoyer_notification(email_dest, sujet, corps):
    try:
        msg = EmailMessage()
        msg.set_content(corps)
        msg['Subject'] = sujet
        msg['From'] = "julienbanze.k@gmail.com"
        msg['To'] = email_dest
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("julienbanze.k@gmail.com", "ncdjibbdcydgyqhu") 
            smtp.send_message(msg)
        return True, "Succès"
    except Exception as e:
        return False, str(e)

# --- CHARGEMENT DES DONNEES ---
@st.cache_data(ttl=60) # Actualise toutes les minutes
def charger_donnees(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        # On s'adapte à tes titres exacts
        data['Identite'] = data['Nom_Eleve'].fillna('') + " " + data['Postnom_Eleve'].fillna('') + " " + data['Prenom_Eleve'].fillna('')
        return data
    except Exception as e:
        st.error(f"Erreur de connexion au Sheets : {e}")
        return None

df_eleves = charger_donnees(URL_ELEVES)

# --- NAVIGATION ---
params = st.query_params
mode_admin = params.get("admin") == "upl"

if mode_admin:
    st.sidebar.title("🛠️ PANEL ADMIN UPL")
    menu = st.sidebar.selectbox("ALLER À :", ["Pointage", "Générer Cartes QR", "Tableau de Bord", "Calcul Bulletin"])
else:
    menu = "Pointage"

# --- 1. PAGE POINTAGE ---
if menu == "Pointage":
    st.title("🚀 Pointage & Alerte Parents")
    
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        mode_scan = st.radio("Méthode d'identification :", ["👤 Visage (IA)", "💳 Carte (QR Code)"], horizontal=True)
        img = st.camera_input("Scanner l'élève")
        
    with col_right:
        st.subheader("Validation")
        mat_input = st.text_input("🔢 Entrez le Matricule :", placeholder="Ex: 2025023061")
        
        if st.button("VALIDER LA PRÉSENCE"):
            if df_eleves is not None and mat_input:
                res = df_eleves[df_eleves['Matricule'].astype(str) == str(mat_input)]
                if not res.empty:
                    eleve = res.iloc[0]
                    with st.spinner('Envoi de la notification au parent...'):
                        heure = datetime.now().strftime("%H:%M")
                        corps = f"UPL INFO : L'étudiant {eleve['Identite']} est arrivé à l'université à {heure}."
                        ok, erreur = envoyer_notification(eleve['Email_Parent'], "🔔 Alerte Présence", corps)
                        
                        if ok:
                            st.success(f"✅ BIENVENU(E) {eleve['Identite']}")
                            st.info(f"📧 Email envoyé à : {eleve['Email_Parent']}")
                            time.sleep(4)
                            st.rerun()
                        else:
                            st.error(f"❌ Email non envoyé. Erreur : {erreur}")
                else:
                    st.error("⚠️ Matricule inconnu. Vérifiez votre Google Sheets.")

# --- 2. PAGE GENERER CARTES ---
elif menu == "Générer Cartes QR":
    st.title("🪪 Création de Cartes d'Étudiant")
    if df_eleves is not None:
        sel = st.selectbox("Choisir l'élève :", df_eleves['Identite'].tolist())
        row = df_eleves[df_eleves['Identite'] == sel].iloc[0]
        
        qr = qrcode.make(str(row['Matricule']))
        buf = BytesIO() # Nécessite 'from io import BytesIO'
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(qr.get_image(), width=250, caption="QR Code à imprimer")
        with col2:
            st.info(f"**NOM :** {row['Nom_Eleve']}\n\n**POSTNOM :** {row['Postnom_Eleve']}\n\n**MATRICULE :** {row['Matricule']}")

# --- 3. PAGE TABLEAU DE BORD (FIXÉ) ---
elif menu == "Tableau de Bord":
    st.title("📋 Liste Complète des Étudiants")
    if df_eleves is not None:
        st.write(f"Nombre total d'élèves : {len(df_eleves)}")
        st.dataframe(df_eleves, use_container_width=True)
    else:
        st.warning("Aucune donnée à afficher. Vérifiez le lien Google Sheets.")

# --- 4. PAGE CALCUL BULLETIN (FIXÉ) ---
elif menu == "Calcul Bulletin":
    st.title("📊 Calculateur de Résultats")
    if df_eleves is not None:
        eleve_sel = st.selectbox("Sélectionner l'élève pour le bulletin :", df_eleves['Identite'].tolist())
        data_el = df_eleves[df_eleves['Identite'] == eleve_sel].iloc[0]
        
        with st.form("notes_form"):
            c1, c2 = st.columns(2)
            math = c1.number_input("Mathématiques /20", 0, 20)
            cours = c2.number_input("Autre Cours /20", 0, 20)
            cote = c1.number_input("Cote de conduite /10", 0, 10)
            
            if st.form_submit_button("CALCULER & ENVOYER LE BULLETIN"):
                total = math + cours + cote
                pourcent = (total / 50) * 100
                st.metric("Résultat Final", f"{pourcent}%", f"{total}/50")
                
                corps_res = f"Résultats UPL de {eleve_sel} :\nTotal: {total}/50\nPourcentage: {pourcent}%\nFélicitations."
                ok, err = envoyer_notification(data_el['Email_Parent'], "📊 Bulletin Numérique", corps_res)
                if ok: st.success("Bulletin envoyé au parent !")
                else: st.error(f"Erreur d'envoi : {err}")
