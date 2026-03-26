import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import time

# --- CONFIGURATION LUBUMBASHI (UTC+2) ---
st.set_page_config(page_title="EduTracer UPL - Correction Matricule", layout="wide", page_icon="☝️")

def get_upl_time():
    """Récupère l'heure exacte de Lubumbashi"""
    return datetime.utcnow() + timedelta(hours=2)

# --- INITIALISATION DES BASES DE DONNÉES ---
DB_E = "base_etudiants.csv"        
DB_P = "registre_presences.csv"     
DB_B = "liaison_biometrique.csv"    

def init_db():
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
    
    finger_sim_id = "ID_BIO_LUBUM_001" 
    
    db_b = pd.read_csv(DB_B)
    db_e = pd.read_csv(DB_E)
    
    # --- CORRECTION CRITIQUE ICI ---
    # On force tous les matricules de la base en TEXTE et on enlève les espaces
    db_e['Matricule'] = db_e['Matricule'].astype(str).str.strip()
    db_b['Matricule'] = db_b['Matricule'].astype(str).str.strip()
    
    liaison = db_b[db_b['Finger_ID'] == finger_sim_id]
    
    if liaison.empty:
        st.warning("🆕 Nouvelle empreinte détectée.")
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            mat_input = st.text_input("Saisissez votre Numéro Matricule :").strip()
            
            if st.button("LIER MON EMPREINTE"):
                # On compare le texte saisi avec le texte de la base
                if mat_input in db_e['Matricule'].values:
                    new_link = pd.DataFrame([{"Matricule": mat_input, "Finger_ID": finger_sim_id}])
                    pd.concat([db_b, new_link]).to_csv(DB_B, index=False)
                    st.success("✅ Empreinte liée avec succès !")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Le matricule '{mat_input}' n'est pas dans la liste des {len(db_e)} inscrits.")
                    st.info("💡 Vérifiez l'onglet Administration pour voir si l'élève est bien inscrit.")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        mat_found = str(liaison.iloc[0]['Matricule'])
        etudiant = db_e[db_e['Matricule'] == mat_found].iloc[0]
        nom_complet = f"{etudiant['Nom_Eleve']} {etudiant['Postnom_Eleve']} {etudiant['Prenom_Eleve']}"
        
        st.info(f"👤 Reconnu : **{nom_complet}**")
        
        if st.button("VALIDER PRÉSENCE (SCAN)"):
            with st.spinner("Analyse..."):
                time.sleep(1)
                today = get_upl_time().strftime("%d/%m/%Y")
                now_t = get_upl_time().strftime("%H:%M")
                db_p = pd.read_csv(DB_P)
                
                row_idx = db_p[(db_p['Matricule'].astype(str) == mat_found) & (db_p['Date'] == today)].index
                
                if len(row_idx) == 0:
                    new_log = pd.DataFrame([{"Matricule": mat_found, "Identite_Complete": nom_complet, "Date": today, "Entree": now_t, "Sortie": None, "Statut": "Partiel"}])
                    pd.concat([db_p, new_log]).to_csv(DB_P, index=False)
                    st.success(f"✅ ENTRÉE : {now_t}")
                else:
                    if pd.isna(db_p.loc[row_idx[0], 'Sortie']):
                        db_p.loc[row_idx[0], 'Sortie'] = now_t
                        db_p.loc[row_idx[0], 'Statut'] = "Présent"
                        db_p.to_csv(DB_P, index=False)
                        st.success(f"✅ SORTIE : {now_t}")
                        st.balloons()

# ---------------------------------------------------------
# 2. ESPACE ADMINISTRATION
# ---------------------------------------------------------
elif role == "🔐 Administration":
    st.title("🔐 Gestion UPL")
    tab_list, tab_add = st.tabs(["👥 Liste", "➕ Ajouter"])
    
    db_e = pd.read_csv(DB_E)
    
    with tab_list:
        st.dataframe(db_e, use_container_width=True)
        if st.button("Vider toute la liste (Reset)"):
            pd.DataFrame(columns=["Matricule", "Nom_Eleve", "Postnom_Eleve", "Prenom_Eleve", "Classe"]).to_csv(DB_E, index=False)
            st.rerun()

    with tab_add:
        with st.form("add"):
            m = st.text_input("Matricule")
            n = st.text_input("Nom_Eleve")
            p = st.text_input("Postnom_Eleve")
            pr = st.text_input("Prenom_Eleve")
            cl = st.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA"])
            if st.form_submit_button("Inscrire"):
                new_row = pd.DataFrame([{"Matricule": str(m).strip(), "Nom_Eleve": n.upper(), "Postnom_Eleve": p.upper(), "Prenom_Eleve": pr, "Classe": cl}])
                pd.concat([db_e, new_row]).to_csv(DB_E, index=False)
                st.success("Ajouté !")
                st.rerun()

# ---------------------------------------------------------
# 3. CALCULATEUR BULLETIN
# ---------------------------------------------------------
else:
    st.title("📊 Calculateur")
    n = st.number_input("Nombre de cours", 1, 10, 5)
    notes = [st.number_input(f"Cours {i+1}", 0, 20, 10) for i in range(n)]
    if st.button("Calculer"):
        st.write(f"## Moyenne : {(sum(notes)/(n*20))*100}%")
