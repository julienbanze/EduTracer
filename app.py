import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
from io import BytesIO
import os
from streamlit_qr_reader import streamlit_qr_reader

# --- CONFIGURATION & DESIGN ---
st.set_page_config(page_title="EduTracer UPL Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f4f8; }
    .card-pro { background-color: white; padding: 25px; border-radius: 15px; border-left: 8px solid #004e92; box-shadow: 0px 10px 20px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES PERSISTANTE ---
FICHIER_PRESENCES = "registre_upl.csv"

def enregistrer_presence(matricule, nom_complet, classe):
    df = pd.read_csv(FICHIER_PRESENCES) if os.path.exists(FICHIER_PRESENCES) else pd.DataFrame(columns=['Matricule', 'Nom_Complet', 'Classe', 'Date', 'Heure'])
    now = datetime.now()
    nouvelle_ligne = {'Matricule': matricule, 'Nom_Complet': nom_complet, 'Classe': classe, 'Date': now.strftime("%d/%m/%Y"), 'Heure': now.strftime("%H:%M:%S")}
    df = pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
    df.to_csv(FICHIER_PRESENCES, index=False)
    return nouvelle_ligne

# --- INTERFACE ADMIN CACHÉE ---
is_admin = st.query_params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE ÉLÈVE : LE SCANNER AUTOMATIQUE
# ---------------------------------------------------------
if not is_admin:
    st.markdown("<h1 style='text-align: center; color: #004e92;'>📲 Scanner QR Code UPL</h1>", unsafe_allow_html=True)
    
    col_scan, col_info = st.columns([1, 1])
    
    with col_scan:
        st.markdown("<div class='card-pro'>", unsafe_allow_html=True)
        st.subheader("Placement du Code QR")
        # Le scanner automatique : il renvoie le texte dès qu'il "voit" le QR
        qr_data = streamlit_qr_reader(key='qrcode_reader')
        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        if qr_data:
            try:
                # On découpe les infos : Matricule|Nom|Classe
                infos = qr_data.split("|")
                mat, nom, cl = infos[0], infos[1], infos[2]
                
                # Enregistrement automatique dès détection
                enregistrer_presence(mat, nom, cl)
                
                st.markdown(f"""
                <div class='card-pro' style='border-left-color: #28a745;'>
                    <h3 style='color: #28a745;'>✅ PRÉSENCE ENREGISTRÉE</h3>
                    <p><b>Étudiant :</b> {nom}</p>
                    <p><b>Classe :</b> {cl}</p>
                    <p><b>ID :</b> {mat}</p>
                    <p style='color: gray;'>Heure : {datetime.now().strftime('%H:%M:%S')}</p>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
            except Exception as e:
                st.error("Format de QR Code non reconnu par le système UPL.")
        else:
            st.info("En attente d'un code QR valide devant la caméra...")

# ---------------------------------------------------------
# INTERFACE ADMIN (GÉNÉRATEUR DE CARTES)
# ---------------------------------------------------------
else:
    st.sidebar.title("👨‍💻 Admin : Julien")
    # ... (Garder le même code pour le générateur de cartes ici)
    # Assure-toi que le générateur crée bien le format : Matricule|Nom|Classe
