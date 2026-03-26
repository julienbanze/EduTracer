import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import time

# --- CONFIGURATION LUBUMBASHI (UTC+2) ---
st.set_page_config(page_title="EduTracer UPL - Format Google Sheets", layout="wide", page_icon="☝️")

def get_upl_time():
    """Récupère l'heure exacte de Lubumbashi"""
    return datetime.utcnow() + timedelta(hours=2)

# --- INITIALISATION DES BASES DE DONNÉES ---
DB_E = "base_etudiants.csv"        # Liste des élèves inscrits
DB_P = "registre_presences.csv"     # Historique des pointages
DB_B = "liaison_biometrique.csv"    # Table Matricule <-> Empreinte

def init_db():
    # Création des fichiers avec les noms de colonnes formatés pour Google Sheets (_Eleve)
    if not os.path.exists(DB_E):
        pd.DataFrame(columns=["Matricule", "Nom_Eleve", "Postnom_Eleve", "Prenom_Eleve", "Classe"]).to_csv(DB_E, index=False)
    
    if not os.path.exists(DB_P):
        pd.DataFrame(columns=["Matricule", "Identite_Complete", "Date", "Entree", "Sortie", "Statut"]).to_csv(DB_P, index=False)
    
    if not os.path.exists(DB_B):
        pd.DataFrame(columns=["Matricule", "Finger_ID"]).to_csv(DB_B, index=False)

init_db()

# --- DESIGN ET STYLE ---
st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    .stButton>button { 
        background: linear-gradient(90deg, #238636 0%, #2ea043 100%); 
        color: white; border-radius: 12px; font-weight: bold; height: 3.5em; width: 100%;
    }
    .card { 
        background: #161B22; border: 1px solid #30363D; 
        padding: 25px; border-radius: 15px; text-align: center;
    }
    h1, h2, h3 { color: #58A6FF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
st.sidebar.markdown("<h2 style='text-align: center;'>🛡️ EduTracer UPL</h2>", unsafe_allow_html=True)
role = st.sidebar.radio("SÉLECTIONNER ESPACE :", ["🎓 Portail Étudiant", "🔐 Administration", "📊 Calculateur Bulletin"])

# ---------------------------------------------------------
# 1. ESPACE ÉTUDIANT
# ---------------------------------------------------------
if role == "🎓 Portail Étudiant":
    st.title("☝️ Pointage Biométrique")
    
    # ID simulé du capteur (Hardware ID)
    finger_sim_id = "ID_BIO_LUBUM_001" 
    
    db_b = pd.read_csv(DB_B)
    db_e = pd.read_csv(DB_E)
    db_e['Matricule'] = db_e['Matricule'].astype(str)
    
    liaison = db_b[db_b['Finger_ID'] == finger_sim_id]
    
    if liaison.empty:
        st.warning("🆕 Nouvelle empreinte. Liaison au matricule requise (Première fois).")
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            mat_input = st.text_input("Saisissez votre Numéro Matricule :").strip()
            if st.button("LIER MON EMPREINTE"):
                if mat_input in db_e['Matricule'].values:
                    new_link = pd.DataFrame([{"Matricule": mat_input, "Finger_ID": finger_sim_id}])
                    pd.concat([db_b, new_link]).to_csv(DB_B, index=False)
                    st.success("✅ Empreinte liée avec succès !")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Ce matricule n'est pas encore enregistré dans le système.")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        mat_found = str(liaison.iloc[0]['Matricule'])
        etudiant = db_e[db_e['Matricule'] == mat_found].iloc[0]
        # Construction de l'identité avec les nouveaux noms de colonnes
        nom_complet = f"{etudiant['Nom_Eleve']} {etudiant['Postnom_Eleve']} {etudiant['Prenom_Eleve']}"
        
        st.info(f"👤 Étudiant reconnu : **{nom_complet}** ({etudiant['Classe']})")
        
        if st.button("VALIDER PRÉSENCE (SCAN EMPREINTE)"):
            with st.spinner("Analyse du doigt..."):
                time.sleep(1)
                today = get_upl_time().strftime("%d/%m/%Y")
                now_t = get_upl_time().strftime("%H:%M")
                db_p = pd.read_csv(DB_P)
                
                row_idx = db_p[(db_p['Matricule'] == mat_found) & (db_p['Date'] == today)].index
                
                if len(row_idx) == 0:
                    # Premier pointage : Entrée
                    new_log = pd.DataFrame([{
                        "Matricule": mat_found, 
                        "Identite_Complete": nom_complet, 
                        "Date": today, 
                        "Entree": now_t, 
                        "Sortie": None, 
                        "Statut": "Partiel"
                    }])
                    pd.concat([db_p, new_log]).to_csv(DB_P, index=False)
                    st.success(f"✅ ENTRÉE ENREGISTRÉE : {now_t}")
                else:
                    # Deuxième pointage : Sortie
                    if pd.isna(db_p.loc[row_idx[0], 'Sortie']):
                        db_p.loc[row_idx[0], 'Sortie'] = now_t
                        db_p.loc[row_idx[0], 'Statut'] = "Présent"
                        db_p.to_csv(DB_P, index=False)
                        st.success(f"✅ SORTIE ENREGISTRÉE : {now_t}")
                        st.balloons()
                    else:
                        st.warning("⚠️ Vous avez déjà validé votre sortie pour aujourd'hui.")

# ---------------------------------------------------------
# 2. ESPACE ADMINISTRATION (GESTION DES ÉLÈVES)
# ---------------------------------------------------------
elif role == "🔐 Administration":
    st.title("🔐 Gestion de la Base de Données UPL")
    
    tab_list, tab_add, tab_pres = st.tabs(["👥 Liste des Élèves", "➕ Inscription Élève", "📋 Journal des Présences"])
    
    db_e = pd.read_csv(DB_E)
    db_p = pd.read_csv(DB_P)

    with tab_list:
        st.write("### Étudiants inscrits (Format Google Sheets)")
        st.dataframe(db_e, use_container_width=True)

    with tab_add:
        st.write("### Ajouter un nouvel étudiant à la base")
        with st.form("ajout_eleve"):
            c1, c2, c3 = st.columns(3)
            new_mat = c1.text_input("Matricule Unique")
            new_nom = c2.text_input("Nom_Eleve")
            new_pos = c3.text_input("Postnom_Eleve")
            new_pre = c1.text_input("Prenom_Eleve")
            new_cla = c2.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA", "L1 INFO", "L2 INFO"])
            
            if st.form_submit_button("VALIDER L'INSCRIPTION"):
                if new_mat and new_nom and new_pre:
                    # Vérifier les doublons de matricule
                    if new_mat in db_e['Matricule'].astype(str).values:
                        st.error("Ce matricule est déjà utilisé !")
                    else:
                        new_data = pd.DataFrame([{
                            "Matricule": new_mat, 
                            "Nom_Eleve": new_nom.upper(), 
                            "Postnom_Eleve": new_pos.upper(),
                            "Prenom_Eleve": new_pre, 
                            "Classe": new_cla
                        }])
                        pd.concat([db_e, new_data]).to_csv(DB_E, index=False)
                        st.success(f"L'élève {new_nom} a été ajouté avec succès.")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("Veuillez remplir au moins le Matricule, le Nom et le Prénom.")

    with tab_pres:
        st.write("### Rapport de présence en temps réel")
        st.dataframe(db_p, use_container_width=True)
        st.download_button("📥 Télécharger le rapport CSV", db_p.to_csv(index=False), "rapport_presences.csv")

# ---------------------------------------------------------
# 3. CALCULATEUR BULLETIN
# ---------------------------------------------------------
else:
    st.title("📊 Calculateur de Moyenne")
    n_mat = st.number_input("Nombre de cours", 1, 15, 5)
    with st.form("calc"):
        notes = [st.number_input(f"Cours {i+1} (/20)", 0, 20, 10) for i in range(n_mat)]
        if st.form_submit_button("CALCULER POURCENTAGE"):
            moyenne = (sum(notes) / (n_mat * 20)) * 100
            st.metric("Résultat Final", f"{round(moyenne, 2)}%")
            if moyenne >= 50: st.success("Réussite")
            else: st.error("Échec")
