import streamlit as st
import pandas as pd
import qrcode
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
import os

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(page_title="UPL EduTracer AI", layout="wide", page_icon="🛡️")

def get_lubumbashi_time():
    # Force le fuseau horaire UTC+2 pour la RDC
    return datetime.utcnow() + timedelta(hours=2)

# --- BASE DE DONNÉES LOCALE (CSV) ---
DB_E = "base_eleves_upl.csv"
DB_P = "registre_presences.csv"

def init_db():
    if not os.path.exists(DB_E):
        # Création d'une base de test si le fichier n'existe pas
        pd.DataFrame([
            {"Matricule": "2025023061", "Nom": "BANZE", "Prenom": "Julien", "Classe": "Bac 1 IA"},
            {"Matricule": "123456", "Nom": "KABAMBA", "Prenom": "Marc", "Classe": "Bac 1 IA"}
        ]).to_csv(DB_E, index=False)
    if not os.path.exists(DB_P):
        pd.DataFrame(columns=["Matricule", "Identite", "Classe", "Date", "Heure"]).to_csv(DB_P, index=False)

init_db()

# --- DESIGN "CYBER-DARK" (LISIBILITÉ MAXIMALE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #CFD8DC; }
    .stHeader { background: transparent; }
    .metric-box { 
        background: #151921; 
        border: 1px solid #2D333B; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.6);
    }
    .stButton>button { 
        background: linear-gradient(135deg, #238636, #2ea043);
        color: white; 
        border: none; 
        border-radius: 8px; 
        font-weight: bold;
        font-size: 16px;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(35, 134, 54, 0.4); }
    input { 
        background-color: #010409 !important; 
        color: #58A6FF !important; 
        border: 1px solid #30363D !important; 
        font-size: 1.1em !important;
    }
    h1, h2, h3 { color: #58A6FF !important; font-family: 'Inter', sans-serif; }
    .stDataFrame { border: 1px solid #30363D; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- SÉCURITÉ ADMIN ---
is_admin = st.query_params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE ÉTUDIANT (PORTAIL DE POINTAGE)
# ---------------------------------------------------------
if not is_admin:
    st.sidebar.markdown("<h2 style='text-align:center;'>🎓 UPL PORTAIL</h2>", unsafe_allow_html=True)
    nav = st.sidebar.radio("NAVIGATION", ["📍 Présence", "📊 Bulletin"])

    if nav == "📍 Présence":
        st.title("🛡️ EduTracer : Pointage Biométrique")
        c1, c2 = st.columns([1.2, 1])
        
        with c1:
            st.camera_input("SCANNER", label_visibility="hidden")
        
        with c2:
            st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
            st.write("### Identification")
            # .strip() pour éviter les erreurs d'espaces invisibles
            mat_check = st.text_input("NUMÉRO MATRICULE", placeholder="Entrez votre ID...").strip()
            
            if st.button("VALIDER MON ARRIVÉE"):
                if mat_check:
                    df_e = pd.read_csv(DB_E)
                    # FIX CRUCIAL : On force la comparaison en texte (String)
                    df_e['Matricule'] = df_e['Matricule'].astype(str)
                    user = df_e[df_e['Matricule'] == mat_check]
                    
                    if not user.empty:
                        u = user.iloc[0]
                        identite = f"{u['Nom']} {u['Prenom']}"
                        t_upl = get_lubumbashi_time()
                        
                        # Enregistrement dans les logs
                        df_p = pd.read_csv(DB_P)
                        new_log = pd.DataFrame([{
                            "Matricule": mat_check, 
                            "Identite": identite, 
                            "Classe": u['Classe'], 
                            "Date": t_upl.strftime("%d/%m/%Y"), 
                            "Heure": t_upl.strftime("%H:%M:%S")
                        }])
                        pd.concat([df_p, new_log]).to_csv(DB_P, index=False)
                        
                        st.success(f"✅ BIENVENUE : {identite}")
                        st.info(f"Enregistré à {t_upl.strftime('%H:%M:%S')} (Lubumbashi)")
                        st.balloons()
                    else:
                        st.error("❌ MATRICULE NON RÉPERTORIÉ. Vérifiez votre saisie.")
                else:
                    st.warning("Veuillez saisir un matricule.")
            st.markdown("</div>", unsafe_allow_html=True)

    elif nav == "📊 Bulletin":
        st.title("📊 Calculateur de Résultats")
        nb_mat = st.number_input("Nombre de matières", 1, 15, 5)
        with st.form("bull"):
            notes, maxs = [], []
            cols = st.columns(2)
            for i in range(int(nb_mat)):
                notes.append(cols[0].number_input(f"Note {i+1}", 0.0, 100.0, 10.0))
                maxs.append(cols[1].number_input(f"Max {i+1}", 1.0, 100.0, 20.0))
            if st.form_submit_button("CALCULER"):
                p = (sum(notes)/sum(maxs)) * 100
                st.markdown(f"<h1 style='text-align:center;'>{round(p, 2)}%</h1>", unsafe_allow_html=True)
                if p >= 80: st.success("EXCELLENT 🌟")
                elif p >= 50: st.info("RÉUSSI ✅")
                else: st.error("ÉCHEC ❌")

# ---------------------------------------------------------
# INTERFACE ADMIN (DASHBOARD EXPERT)
# ---------------------------------------------------------
else:
    st.sidebar.markdown("<h2 style='color:#58A6FF;'>💎 ADMIN DASHBOARD</h2>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 DÉCONNEXION"):
        st.query_params.clear()
        st.rerun()

    menu = st.radio("SÉLECTIONNER UNE TÂCHE :", ["📈 Statistiques", "👥 Scolarité", "⚙️ Maintenance"], horizontal=True)
    st.divider()

    if menu == "📈 Statistiques":
        df_p = pd.read_csv(DB_P)
        df_e = pd.read_csv(DB_E)
        
        # MÉTROQUES CLÉS
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-box'><p>INSCRITS</p><h2>{len(df_e)}</h2></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-box'><p>PRÉSENTS</p><h2>{len(df_p)}</h2></div>", unsafe_allow_html=True)
        t_p = (len(df_p)/len(df_e)*100) if len(df_e)>0 else 0
        m3.markdown(f"<div class='metric-box'><p>TAUX</p><h2>{round(t_p, 1)}%</h2></div>", unsafe_allow_html=True)

        if not df_p.empty:
            c_g, c_t = st.columns([1, 1.5])
            with c_g:
                st.write("#### Présences par Classe")
                fig, ax = plt.subplots(facecolor='#151921')
                counts = df_p['Classe'].value_counts()
                ax.pie(counts, labels=counts.index, autopct='%1.1f%%', textprops={'color':"w"}, colors=['#58A6FF', '#238636', '#D29922'])
                st.pyplot(fig)
            with c_t:
                st.write("#### Logs Récents")
                st.dataframe(df_p.tail(10), use_container_width=True)
        else:
            st.info("Aucun log disponible.")

    elif menu == "👥 Scolarité":
        st.subheader("Gestion des Étudiants")
        with st.expander("➕ Ajouter un Étudiant"):
            with st.form("add"):
                c1, c2, c3 = st.columns(3)
                m = c1.text_input("Matricule")
                n = c2.text_input("Nom")
                cl = c3.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA", "L1 INFO"])
                if st.form_submit_button("Enregistrer"):
                    df = pd.read_csv(DB_E)
                    pd.concat([df, pd.DataFrame([{"Matricule":m, "Nom":n.upper(), "Prenom":"", "Classe":cl}])]).to_csv(DB_E, index=False)
                    st.success("Étudiant ajouté !")
                    st.rerun()

        st.dataframe(pd.read_csv(DB_E), use_container_width=True)
        
        st.divider()
        st.write("### 🗑️ Suppression")
        del_m = st.text_input("Matricule à supprimer")
        if st.button("SUPPRIMER"):
            df = pd.read_csv(DB_E)
            df[df['Matricule'].astype(str) != del_m].to_csv(DB_E, index=False)
            st.warning(f"Matricule {del_m} supprimé.")
            st.rerun()

    elif menu == "⚙️ Maintenance":
        if st.button("🔥 RÉINITIALISER TOUS LES LOGS"):
            pd.DataFrame(columns=["Matricule", "Identite", "Classe", "Date", "Heure"]).to_csv(DB_P, index=False)
            st.success("Registre vidé.")
