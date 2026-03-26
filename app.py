import streamlit as st
import pandas as pd
import qrcode
import cv2
import numpy as np
from datetime import datetime
from io import BytesIO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# --- CONFIGURATION ---
st.set_page_config(page_title="EduTracer UPL Pro", layout="wide")

# Simulation de base de données locale (CSV)
FICHIER = "registre_upl.csv"
if 'db' not in st.session_state:
    if not hasattr(st, "db_loaded"):
        try:
            st.session_state.db = pd.read_csv(FICHIER)
        except:
            st.session_state.db = pd.DataFrame(columns=['Matricule', 'Nom_Complet', 'Classe', 'Date', 'Heure'])
        st.db_loaded = True

# --- LOGIQUE DE SCAN QR ---
class QRScanner(VideoTransformerBase):
    def __init__(self):
        self.detector = cv2.QRCodeDetector()

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        data, bbox, _ = self.detector.detectAndDecode(img)
        if data:
            st.session_state.last_qr = data
        return img

# --- INTERFACE ADMIN (Accès par mot de passe ou paramètre) ---
# On utilise un bouton simple pour la démo si l'URL ne passe pas
is_admin = st.sidebar.checkbox("Accès Administrateur (Julien)")

# ---------------------------------------------------------
# INTERFACE ÉLÈVE : SCANNER QR TEMPS RÉEL
# ---------------------------------------------------------
if not is_admin:
    st.title("🛡️ UPL - Scanner de Présence")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📷 Placez votre carte ici")
        webrtc_streamer(key="scanner", video_transformer_factory=QRScanner)
        
    with col2:
        st.subheader("📄 Résultat du Scan")
        if "last_qr" in st.session_state:
            try:
                # Format attendu : Matricule|Nom|Postnom|Prenom|Classe
                d = st.session_state.last_qr.split("|")
                mat, nom, pnom, pren, cl = d[0], d[1], d[2], d[3], d[4]
                nom_c = f"{nom} {pnom} {pren}"
                
                st.success(f"✅ Identifié : {nom_c}")
                st.write(f"**Classe :** {cl}")
                
                # Enregistrement
                now = datetime.now()
                new_data = pd.DataFrame([[mat, nom_c, cl, now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S")]], 
                                        columns=st.session_state.db.columns)
                st.session_state.db = pd.concat([st.session_state.db, new_data], ignore_index=True)
                st.session_state.db.to_csv(FICHIER, index=False)
                st.balloons()
                del st.session_state.last_qr # Reset pour le prochain
            except:
                st.error("QR Code non valide ou mal formaté.")

# ---------------------------------------------------------
# INTERFACE ADMIN : GÉNÉRATEUR & SUIVI
# ---------------------------------------------------------
else:
    st.title("⚙️ Gestion Administrative - Julien")
    tab1, tab2 = st.tabs(["🪪 Générer Carte", "📊 Suivi Présences"])

    with tab1:
        with st.form("carte"):
            c1, c2 = st.columns(2)
            m = c1.text_input("Matricule")
            n = c2.text_input("Nom")
            pn = c1.text_input("Postnom")
            pr = c2.text_input("Prénom")
            cl = st.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA", "L1 INFO"])
            if st.form_submit_button("Générer la Carte Complète"):
                # QR Data : On met TOUT dedans pour que le scanner lise tout
                qr_data = f"{m}|{n}|{pn}|{pr}|{cl}"
                img_qr = qrcode.make(qr_data)
                
                # Affichage de la carte
                st.markdown(f"""
                <div style="border:2px solid #000; padding:15px; border-radius:10px; background:#fff; width:350px;">
                    <h3 style="color:#004e92; text-align:center;">UPL - CARTE ÉLÈVE</h3>
                    <p><b>Nom :</b> {n.upper()}</p>
                    <p><b>Postnom :</b> {pn.upper()}</p>
                    <p><b>Prénom :</b> {pr.title()}</p>
                    <p><b>Classe :</b> {cl}</p>
                    <p><b>Matricule :</b> {m}</p>
                </div>
                """, unsafe_allow_html=True)
                st.image(img_qr.get_image(), width=150)

    with tab2:
        st.subheader("Liste des présences")
        st.dataframe(st.session_state.db, use_container_width=True)
