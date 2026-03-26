import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime
import time

# --- 1. CONFIGURATION DES SOURCES ---
ID_SHEET = "1ROnvyK-h9I8mzAsfGjSRiQz8HLf5MppGVMCMt_vpiuM"
# Onglet 'Eleves' (gid=0)
URL_ELEVES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"

st.set_page_config(page_title="EduTracer UPL", layout="wide", page_icon="🎓")

# --- 2. STOCKAGE TEMPORAIRE DES ACTIONS (SESSION) ---
if 'histo_presences' not in st.session_state:
    st.session_state.histo_presences = []
if 'histo_resultats' not in st.session_state:
    st.session_state.histo_resultats = []

# --- 3. FONCTION ENVOI EMAIL (Code: ncjzdgdxnplcptjj) ---
def envoyer_mail(email_dest, sujet, corps):
    try:
        msg = EmailMessage()
        msg.set_content(corps)
        msg['Subject'] = sujet
        msg['From'] = "julienbanze.k@gmail.com"
        msg['To'] = email_dest
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("julienbanze.k@gmail.com", "ncjzdgdxnplcptjj") 
            smtp.send_message(msg)
        return True
    except: return False

# --- 4. CHARGEMENT DYNAMIQUE ---
@st.cache_data(ttl=5)
def charger_data():
    try:
        data = pd.read_csv(URL_ELEVES)
        data.columns = data.columns.str.strip()
        data['Identite'] = data['Nom_Eleve'].astype(str) + " " + data['Postnom_Eleve'].astype(str) + " " + data['Prenom_Eleve'].astype(str)
        return data
    except: return None

df_base = charger_data()

# --- 5. INTERFACE ---
st.sidebar.title("💎 EDU-TRACER UPL")
menu = st.sidebar.radio("Navigation :", ["📍 Pointage Présence", "📊 Onglet Présences", "📝 Onglet Résultats", "👥 Base Élèves"])

if df_base is None:
    st.error("Impossible de charger le fichier Google Sheets. Vérifiez le lien.")
else:
    # --- PAGE : POINTAGE ---
    if menu == "📍 Pointage Présence":
        st.title("📸 Identification & Alerte Parent")
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.camera_input("Scanner le visage")
        with c2:
            mat = st.text_input("Matricule :")
            if st.button("VALIDER L'ENTRÉE", use_container_width=True):
                res = df_base[df_base['Matricule'].astype(str) == str(mat)]
                if not res.empty:
                    el = res.iloc[0]
                    now = datetime.now()
                    # Archivage Présence
                    st.session_state.histo_presences.append({
                        "Matricule": mat, "Nom_Eleve": el['Nom_Eleve'], "PostNom_Eleve": el['Postnom_Eleve'],
                        "Prenom_Eleve": el['Prenom_Eleve'], "Date": now.strftime("%d/%m/%Y"),
                        "Heure": now.strftime("%H:%M"), "Statut": "Présent"
                    })
                    # Email
                    envoyer_mail(el['Email_Parent'], "🔔 Présence UPL", f"{el['Identite']} est arrivé à l'UPL à {now.strftime('%H:%M')}.")
                    st.success(f"✅ BIENVENU {el['Identite']}")
                    time.sleep(2)
                    st.rerun()

    # --- PAGE : ONGLET PRÉSENCES ---
    elif menu == "📊 Onglet Présences":
        st.title("📝 Registre Journalier")
        if st.session_state.histo_presences:
            st.table(pd.DataFrame(st.session_state.histo_presences))
        else: st.info("Aucune présence aujourd'hui.")

    # --- PAGE : ONGLET RÉSULTATS (DYNAMIQUE) ---
    elif menu == "📝 Onglet Résultats":
        st.title("📊 Calculateur de Bulletin")
        eleve_sel = st.selectbox("Sélectionner l'étudiant :", df_base['Identite'].tolist())
        info_el = df_base[df_base['Identite'] == eleve_sel].iloc[0]
        
        with st.form("form_notes"):
            col_a, col_b = st.columns(2)
            math = col_a.number_input("Math /20", 0, 20, 10)
            cours = col_b.number_input("Cours /20", 0, 20, 10)
            cote = col_a.number_input("Cote /10", 0, 10, 5)
            
            if st.form_submit_button("CALCULER & ENREGISTRER"):
                total = math + cours + cote
                pourcent = (total / 50) * 100
                
                # Archivage Résultat avec TES colonnes
                st.session_state.histo_resultats.append({
                    "Matricule": info_el['Matricule'], "Nom_Eleve": info_el['Nom_Eleve'],
                    "PostNom_Eleve": info_el['Postnom_Eleve'], "Prenom_Eleve": info_el['Prenom_Eleve'],
                    "Math": math, "Cours": cours, "Cote": cote, "Total": total, "Pourcentage": f"{pourcent}%"
                })
                
                # Email Parent
                corps_res = f"Résultats de {eleve_sel} :\nTotal: {total}/50\nPourcentage: {pourcent}%"
                envoyer_mail(info_el['Email_Parent'], "📊 Bulletin Numérique", corps_res)
                st.success(f"Bulletin de {eleve_sel} envoyé au parent !")

        if st.session_state.histo_resultats:
            st.divider()
            st.subheader("Tableau des Résultats Générés")
            st.dataframe(pd.DataFrame(st.session_state.histo_resultats))

    # --- PAGE : BASE ÉLÈVES ---
    elif menu == "👥 Base Élèves":
        st.title("📑 Liste des Inscrits")
        st.dataframe(df_base[['Matricule', 'Nom_Eleve', 'Postnom_Eleve', 'Prenom_Eleve', 'Classe', 'Email_Parent']], use_container_width=True)
