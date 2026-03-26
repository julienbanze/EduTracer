import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# --- CONFIGURATION UPL LUBUMBASHI ---
st.set_page_config(page_title="UPL AI - EduTracer", layout="wide")

# ⚠️ REMPLACE CETTE URL PAR TON LIEN GOOGLE SHEETS "PARTAGÉ"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1vC3Sre8W6u7V9pW6_B3_o5X_L_zK6pM8/edit#gid=0"

def get_upl_time():
    # Heure de Lubumbashi (UTC+2)
    return datetime.utcnow() + timedelta(hours=2)

# --- CONNEXION GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5) # Rafraîchissement toutes les 5 secondes pour tes tests
def charger_feuille(nom_feuille):
    try:
        # Lecture de la feuille spécifique
        return conn.read(spreadsheet=SHEET_URL, worksheet=nom_feuille)
    except Exception as e:
        st.error(f"Impossible de lire la feuille '{nom_feuille}'. Vérifie le nom dans Google Sheets.")
        return pd.DataFrame()

# --- DESIGN DARK MODE (PROFESSIONNEL) ---
st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    .card { background: #161B22; border: 1px solid #30363D; padding: 20px; border-radius: 12px; margin-bottom: 15px; }
    .stButton>button { background: #238636; color: white; border: none; font-weight: bold; width: 100%; height: 3.5em; border-radius: 8px; }
    .stTextInput>div>div>input { background: #0D1117; color: white; border: 1px solid #30363D; }
    h1, h2, h3 { color: #58A6FF; }
    </style>
    """, unsafe_allow_html=True)

# --- SECURITÉ ADMIN ---
is_admin = st.query_params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE ÉTUDIANT
# ---------------------------------------------------------
if not is_admin:
    st.sidebar.title("🎓 Portail Étudiant")
    nav = st.sidebar.radio("Navigation", ["📸 Pointage Présence", "📊 Consulter Bulletin"])

    if nav == "📸 Pointage Présence":
        st.title("🛡️ Pointage Biométrique UPL")
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            st.camera_input("SCANNER FACE ID", label_visibility="hidden")
        
        with c2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.write("### Authentification")
            mat_id = st.text_input("NUMÉRO MATRICULE", placeholder="Ex: 2025023061")
            
            if st.button("VALIDER MON POINTAGE"):
                # On charge les données de la feuille Resultats (pour l'identité)
                df_res = charger_feuille("Resultats")
                
                if not df_res.empty:
                    # NETTOYAGE CRITIQUE : on force tout en texte et on enlève les espaces
                    df_res['Matricule'] = df_res['Matricule'].astype(str).str.strip()
                    valeur_cherchee = str(mat_id).strip()
                    
                    match = df_res[df_res['Matricule'] == valeur_cherchee]
                    
                    if not match.empty:
                        u = match.iloc[0]
                        t = get_upl_time()
                        
                        st.success(f"✅ IDENTITÉ CONFIRMÉE")
                        st.markdown(f"""
                        **Étudiant :** {u['Nom_Eleve']} {u['Prenom_Eleve']}  
                        **Heure local :** {t.strftime('%H:%M:%S')}  
                        **Statut :** Présent enregistré.
                        """)
                        st.balloons()
                    else:
                        st.error("❌ Étudiant non répertorié dans 'Resultats'.")
                        with st.expander("Voir les matricules disponibles"):
                            st.write(df_res['Matricule'].tolist())
                else:
                    st.warning("La base de données est vide ou inaccessible.")
            st.markdown("</div>", unsafe_allow_html=True)

    elif nav == "📊 Consulter Bulletin":
        st.title("📊 Mes Résultats Académiques")
        mat_search = st.text_input("Entrez votre matricule :")
        
        if mat_search:
            df_res = charger_feuille("Resultats")
            if not df_res.empty:
                df_res['Matricule'] = df_res['Matricule'].astype(str).str.strip()
                resultats = df_res[df_res['Matricule'] == str(mat_search).strip()]
                
                if not resultats.empty:
                    st.write(f"### Résultats de : {resultats.iloc[0]['Nom_Eleve']}")
                    # On affiche les colonnes demandées
                    st.dataframe(resultats[['Cours', 'Cote', 'Total', 'Pourcentage']], use_container_width=True)
                else:
                    st.error("Aucun résultat trouvé.")

# ---------------------------------------------------------
# INTERFACE ADMIN
# ---------------------------------------------------------
else:
    st.title("👨‍💼 Dashboard Admin - Julien")
    if st.sidebar.button("🚪 Déconnexion"):
        st.query_params.clear()
        st.rerun()

    choix = st.radio("ACTIONS :", ["📈 Suivi Présences", "📝 Liste Resultats"], horizontal=True)

    if choix == "📈 Suivi Présences":
        df_p = charger_feuille("Presences")
        if not df_p.empty:
            st.write("### Journal de la feuille 'Presences'")
            st.dataframe(df_p, use_container_width=True)
            
            # Graphique rapide
            if 'Statut' in df_p.columns:
                fig, ax = plt.subplots(facecolor='#0D1117')
                df_p['Statut'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax, textprops={'color':"w"})
                st.pyplot(fig)
        else:
            st.info("Aucune donnée dans la feuille 'Presences'.")

    elif choix == "📝 Liste Resultats":
        df_r = charger_feuille("Resultats")
        if not df_r.empty:
            st.write("### Base des notes (Feuille 'Resultats')")
            st.dataframe(df_r, use_container_width=True)
        else:
            st.info("Feuille 'Resultats' introuvable.")
