import streamlit as st
import pandas as pd
import qrcode
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="UPL AI - EduTracer", layout="wide")

def get_upl_time():
    return datetime.utcnow() + timedelta(hours=2)

DB_E = "students_upl.csv"
DB_P = "attendance_upl.csv"

def init_db():
    if not os.path.exists(DB_E):
        pd.DataFrame(columns=["Matricule", "Nom_Eleve", "Prenom_Eleve", "Classe"]).to_csv(DB_E, index=False)
    if not os.path.exists(DB_P):
        pd.DataFrame(columns=["Matricule", "Identite", "Classe", "Date", "Heure"]).to_csv(DB_P, index=False)

init_db()

# --- DESIGN DARK MODE ---
st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    .metric-card { background: #161B22; border: 1px solid #30363D; padding: 15px; border-radius: 10px; text-align: center; }
    .stButton>button { background: #238636; color: white; border-radius: 6px; font-weight: bold; width: 100%; }
    input { background-color: #010409 !important; color: #58A6FF !important; border: 1px solid #30363D !important; }
    h1, h2, h3 { color: #58A6FF !important; }
    </style>
    """, unsafe_allow_html=True)

is_admin = st.query_params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE CLIENT (POINTAGE)
# ---------------------------------------------------------
if not is_admin:
    st.sidebar.title("🎓 UPL ÉTUDIANT")
    nav = st.sidebar.radio("Navigation", ["📸 Présence", "📊 Bulletin"])

    if nav == "📸 Présence":
        st.title("🛡️ Pointage Biométrique")
        c1, c2 = st.columns([1.2, 1])
        with c1: st.camera_input("Scanner", label_visibility="hidden")
        with c2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            mat_id = st.text_input("MATRICULE").strip()
            if st.button("VALIDER"):
                df_e = pd.read_csv(DB_E)
                df_e['Matricule'] = df_e['Matricule'].astype(str)
                user = df_e[df_e['Matricule'] == mat_id]
                if not user.empty:
                    u = user.iloc[0]
                    t = get_upl_time()
                    df_p = pd.read_csv(DB_P)
                    new_p = pd.DataFrame([{"Matricule": mat_id, "Identite": f"{u['Nom']} {u['Prenom']}", "Classe": u['Classe'], "Date": t.strftime("%d/%m/%Y"), "Heure": t.strftime("%H:%M:%S")}])
                    pd.concat([df_p, new_p]).to_csv(DB_P, index=False)
                    st.success(f"✅ Bonjour {u['Prenom']} !")
                else: st.error("Inconnu")
            st.markdown("</div>", unsafe_allow_html=True)

    elif nav == "📊 Bulletin":
        st.title("📊 Calculateur")
        # ... (code bulletin identique aux versions précédentes)

# ---------------------------------------------------------
# INTERFACE ADMIN (GESTION & GÉNÉRATEUR DE CARTE)
# ---------------------------------------------------------
else:
    st.sidebar.title("💎 ADMIN UPL")
    if st.sidebar.button("🚪 Déconnexion"):
        st.query_params.clear()
        st.rerun()

    task = st.radio("TÂCHE :", ["📊 Logs", "👥 Scolarité & Cartes", "⚙️ Système"], horizontal=True)

    if task == "📊 Logs":
        df_p = pd.read_csv(DB_P)
        st.dataframe(df_p, use_container_width=True)
        # Graphique
        if not df_p.empty:
            fig, ax = plt.subplots(facecolor='#161B22')
            df_p['Classe'].value_counts().plot.pie(autopct='%1.1f%%', ax=ax, textprops={'color':"w"})
            st.pyplot(fig)

    elif task == "👥 Scolarité & Cartes":
        st.subheader("Générateur de Carte d'Étudiant Officielle")
        
        with st.form("card_gen"):
            col1, col2 = st.columns(2)
            mat = col1.text_input("Matricule")
            nom = col2.text_input("Nom")
            pre = col1.text_input("Prénom")
            cla = col2.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA", "L1 INFO"])
            
            submit = st.form_submit_button("🔨 GÉNÉRER LA CARTE & ENREGISTRER")
            
            if submit and mat and nom:
                # 1. Sauvegarder dans la base
                df = pd.read_csv(DB_E)
                pd.concat([df, pd.DataFrame([{"Matricule":mat, "Nom":nom.upper(), "Prenom":pre, "Classe":cla}])]).to_csv(DB_E, index=False)
                
                # 2. Création Visuelle de la Carte (Image)
                img = Image.new('RGB', (500, 300), color='#FFFFFF')
                draw = ImageDraw.Draw(img)
                
                # Design de la carte
                draw.rectangle([0, 0, 500, 60], fill='#004e92') # Barre du haut
                draw.text((20, 15), "UNIVERSITÉ PROTESTANTE DE LUBUMBASHI", fill='white')
                draw.text((20, 80), f"NOM : {nom.upper()}", fill='black')
                draw.text((20, 110), f"PRÉNOM : {pre}", fill='black')
                draw.text((20, 140), f"CLASSE : {cla}", fill='black')
                draw.text((20, 170), f"MATRICULE : {mat}", fill='blue')
                
                # 3. Génération du QR Code intégré
                qr = qrcode.make(f"UPL-{mat}")
                qr = qr.resize((120, 120))
                img.paste(qr, (350, 80)) # Positionner le QR code à droite
                
                # Affichage
                st.image(img, caption="Carte d'étudiant générée")
                
                # Bouton de téléchargement
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.download_button("📥 Télécharger la Carte (PNG)", buf.getvalue(), f"Carte_{mat}.png")
                st.success("Étudiant ajouté et carte créée !")

    elif task == "⚙️ Système":
        if st.button("🔥 VIDER LES LOGS"):
            pd.DataFrame(columns=["Matricule", "Identite", "Classe", "Date", "Heure"]).to_csv(DB_P, index=False)
            st.rerun()
