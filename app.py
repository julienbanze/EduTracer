import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
from io import BytesIO
import os

# --- CONFIGURATION DU DESIGN ---
st.set_page_config(page_title="UPL EduTracer", layout="centered")

# CSS pour cacher les éléments inutiles et faire un design pro
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div.block-container { padding-top: 2rem; }
    .stButton>button { background: linear-gradient(135deg, #004e92, #000428); color: white; border-radius: 10px; border: none; }
    .card { background: #1e1e1e; padding: 15px; border-radius: 10px; border-left: 5px solid #004e92; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES ---
FICHIER = "registre_upl.csv"

def enregistrer_scan(data):
    try:
        # Format attendu dans le QR : Matricule|Nom|Classe
        infos = data.split("|")
        df = pd.read_csv(FICHIER) if os.path.exists(FICHIER) else pd.DataFrame(columns=['Matricule', 'Nom', 'Classe', 'Date', 'Heure'])
        nouvelle_ligne = pd.DataFrame([{
            'Matricule': infos[0], 'Nom': infos[1], 'Classe': infos[2],
            'Date': datetime.now().strftime("%d/%m/%Y"),
            'Heure': datetime.now().strftime("%H:%M:%S")
        }])
        pd.concat([df, nouvelle_ligne], ignore_index=True).to_csv(FICHIER, index=False)
        return infos
    except:
        return None

# --- LE FIX DE L'URL (NOUVELLE MÉTHODE) ---
# Accès via : https://ton-app.streamlit.app/?admin=julien
admin_param = st.query_params.get("admin")
is_admin = admin_param == "julien"

# ---------------------------------------------------------
# INTERFACE ÉLÈVE (PAR DÉFAUT)
# ---------------------------------------------------------
if not is_admin:
    st.markdown("<h2 style='text-align: center;'>🛡️ UPL - Scanner</h2>", unsafe_allow_html=True)
    
    # Zone de Scan (Photo pour éviter le bug du lecteur vidéo)
    st.markdown("<div class='card'>📷 <b>Placez votre carte QR</b></div>", unsafe_allow_html=True)
    img = st.camera_input("Scanner", label_visibility="collapsed")
    
    # Résultat du Scan
    st.markdown("### 📄 Résultat")
    # Champ de détection (Automatisé par ton futur script de lecture)
    qr_data = st.text_input("Contenu détecté :", placeholder="Matricule|Nom|Classe")
    
    if qr_data:
        res = enregistrer_scan(qr_data)
        if res:
            st.success(f"Bienvenue, {res[1]} !")
            st.markdown(f"""
            <div class='card' style='border-left-color: #28a745;'>
                <b>{res[1]}</b><br>
                {res[2]} - {res[0]}<br>
                <small>Enregistré à {datetime.now().strftime('%H:%M')}</small>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
        else:
            st.error("Format QR invalide")

# ---------------------------------------------------------
# INTERFACE ADMIN (CACHÉE)
# ---------------------------------------------------------
else:
    st.sidebar.title("💎 Session Admin")
    page = st.sidebar.radio("Menu", ["📊 Présences", "🪪 Créer Carte"])
    
    if page == "📊 Présences":
        st.title("📋 Registre UPL")
        if os.path.exists(FICHIER):
            df_admin = pd.read_csv(FICHIER)
            st.dataframe(df_admin, use_container_width=True)
            st.download_button("Télécharger CSV", df_admin.to_csv(index=False), "registre.csv")
        else:
            st.info("Aucune présence.")
            
    elif page == "🪪 Créer Carte":
        st.title("Générateur QR")
        with st.form("gen"):
            m = st.text_input("Matricule")
            n = st.text_input("Nom Complet")
            c = st.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA"])
            if st.form_submit_button("Générer"):
                data = f"{m}|{n}|{c}"
                qr = qrcode.make(data)
                buf = BytesIO()
                qr.save(buf, format="PNG")
                st.image(buf, width=200)
                st.code(data) # Pour copier-coller dans le test de scan
