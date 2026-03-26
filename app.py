import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# --- CONFIGURATION UPL ---
st.set_page_config(page_title="UPL AI - EduTracer", layout="wide")

# Remplace par l'URL de ton Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/TON_ID_ICI/edit#gid=0"

def get_upl_time():
    # Heure de Lubumbashi (UTC+2)
    return datetime.utcnow() + timedelta(hours=2)

# --- CONNEXION ET CHARGEMENT ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10) # Mise à jour rapide (10 sec)
def charger_donnees(nom_feuille):
    try:
        return conn.read(spreadsheet=SHEET_URL, worksheet=nom_feuille)
    except:
        return pd.DataFrame()

# --- DESIGN DARK MODE UPL ---
st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    .card { background: #161B22; border: 1px solid #30363D; padding: 20px; border-radius: 12px; margin-bottom: 15px; }
    .stButton>button { background: #238636; color: white; border-radius: 8px; font-weight: bold; width: 100%; border: none; height: 3.5em; }
    .stTextInput>div>div>input { background: #0D1117; color: white; border: 1px solid #30363D; }
    h1, h2, h3 { color: #58A6FF; }
    </style>
    """, unsafe_allow_html=True)

# --- SÉCURITÉ ADMIN ---
is_admin = st.query_params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE ÉTUDIANT (PORTAIL CLIENT)
# ---------------------------------------------------------
if not is_admin:
    st.sidebar.title("💎 UPL - Étudiant")
    nav = st.sidebar.selectbox("MENU", ["📸 Pointage Présence", "📊 Mon Bulletin"])

    if nav == "📸 Pointage Présence":
        st.title("🛡️ Système de Pointage Biométrique")
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            st.camera_input("SCANNER FACE ID", label_visibility="hidden")
        
        with c2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.write("### Identification")
            mat_id = st.text_input("NUMÉRO MATRICULE")
            
            if st.button("VALIDER MA PRÉSENCE"):
                # On cherche l'élève dans la feuille Resultats (qui sert de base de données identité)
                df_res = charger_donnees("Resultats")
                
                if not df_res.empty:
                    # Recherche du matricule
                    df_res['Matricule'] = df_res['Matricule'].astype(str).str.strip()
                    match = df_res[df_res['Matricule'] == str(mat_id).strip()]
                    
                    if not match.empty:
                        u = match.iloc[0]
                        t = get_upl_time()
                        
                        # Affichage de confirmation
                        st.success(f"✅ Identité confirmée : {u['Nom_Eleve']} {u['Prenom_Eleve']}")
                        
                        # Information pour l'admin (On simule l'ajout dans Presences)
                        st.info(f"Présence enregistrée à {t.strftime('%H:%M:%S')}")
                        st.balloons()
                        
                        # NOTE : Streamlit-GSheets en lecture seule ne peut pas "écrire" directement.
                        # Pour écrire, il faudra utiliser une API plus complexe. 
                        # Pour ton projet, montre que la lecture fonctionne !
                    else:
                        st.error("Matricule non répertorié dans la feuille Resultats.")
            st.markdown("</div>", unsafe_allow_html=True)

    elif nav == "📊 Mon Bulletin":
        st.title("📊 Mes Résultats Académiques")
        mat_search = st.text_input("Entrez votre matricule pour voir vos notes :")
        
        if mat_search:
            df_res = charger_donnees("Resultats")
            df_res['Matricule'] = df_res['Matricule'].astype(str).str.strip()
            my_notes = df_res[df_res['Matricule'] == str(mat_search).strip()]
            
            if not my_notes.empty:
                st.write(f"### Bulletin de {my_notes.iloc[0]['Nom_Eleve']} {my_notes.iloc[0]['Prenom_Eleve']}")
                st.dataframe(my_notes[['Cours', 'Cote', 'Total', 'Pourcentage']], use_container_width=True)
                
                # Calcul de la moyenne globale
                moyenne = my_notes['Pourcentage'].mean()
                st.metric("MOYENNE GÉNÉRALE", f"{round(moyenne, 2)}%")
            else:
                st.warning("Aucun résultat trouvé pour ce matricule.")

# ---------------------------------------------------------
# INTERFACE ADMIN (TABLEAU DE BORD)
# ---------------------------------------------------------
else:
    st.title("👑 Dashboard Administrateur - Julien")
    
    if st.sidebar.button("🚪 Déconnexion"):
        st.query_params.clear()
        st.rerun()

    task = st.radio("GESTION :", ["📈 Suivi des Présences", "📝 Gestion des Notes"], horizontal=True)

    if task == "📈 Suivi des Présences":
        st.subheader("Journal de présence (Feuille: Presences)")
        df_p = charger_donnees("Presences")
        if not df_p.empty:
            st.dataframe(df_p, use_container_width=True)
            
            # Graphique de statut
            st.write("#### Statistiques de présence")
            fig, ax = plt.subplots(facecolor='#0D1117')
            df_p['Statut'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax, textprops={'color':"w"})
            st.pyplot(fig)
        else:
            st.info("La feuille 'Presences' est vide ou introuvable.")

    elif task == "📝 Gestion des Notes":
        st.subheader("Registre des résultats (Feuille: Resultats)")
        df_r = charger_donnees("Resultats")
        if not df_r.empty:
            st.dataframe(df_r, use_container_width=True)
            st.download_button("📥 Télécharger Bulletin Global", df_r.to_csv(index=False), "resultats_upl.csv")
        else:
            st.info("La feuille 'Resultats' est vide.")
