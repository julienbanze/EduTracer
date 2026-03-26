import streamlit as st
import pandas as pd
import qrcode
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
import os

# --- CONFIGURATION LUBUMBASHI (UTC+2) ---
st.set_page_config(page_title="UPL AI - EduTracer", layout="wide")

def get_upl_time():
    return datetime.utcnow() + timedelta(hours=2)

# --- INITIALISATION BDD ---
DB_E = "students_upl.csv"
DB_P = "attendance_upl.csv"

def init_db():
    if not os.path.exists(DB_E):
        pd.DataFrame(columns=["Matricule", "Nom", "Postnom", "Prenom", "Classe"]).to_csv(DB_E, index=False)
    if not os.path.exists(DB_P):
        pd.DataFrame(columns=["Matricule", "Identite", "Classe", "Date", "Heure"]).to_csv(DB_P, index=False)

init_db()

# --- DESIGN DARK MODE EXPERT ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .metric-card { background: #161B22; border: 1px solid #30363D; padding: 15px; border-radius: 10px; text-align: center; }
    .stButton>button { background: #238636; color: white; border: none; border-radius: 6px; width: 100%; height: 3em; font-weight: bold; }
    .stButton>button:hover { background: #2EA043; border: 1px solid #7EE787; }
    .stTextInput>div>div>input { background-color: #0D1117; color: white; border: 1px solid #30363D; }
    h1, h2, h3 { color: #58A6FF; }
    </style>
    """, unsafe_allow_html=True)

# --- SÉCURITÉ ADMIN ---
is_admin = st.query_params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE CLIENT (ÉLÈVES)
# ---------------------------------------------------------
if not is_admin:
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/d/d5/Logo_UPL.png", width=100) # Remplace par ton logo UPL
    nav = st.sidebar.selectbox("MENU ÉTUDIANT", ["🛡️ Pointage Présence", "📊 Calcul Bulletin"])

    if nav == "🛡️ Pointage Présence":
        st.title("🛡️ EduTracer : Biométrie Faciale")
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            st.camera_input("SCANNER", label_visibility="hidden")
        
        with c2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.write("### Identification")
            mat_id = st.text_input("MATRICULE", placeholder="Ex: 2025023061")
            
            if st.button("ENREGISTRER PRÉSENCE"):
                df_e = pd.read_csv(DB_E)
                user = df_e[df_e['Matricule'].astype(str) == mat_id]
                
                if not user.empty:
                    u = user.iloc[0]
                    nom_c = f"{u['Nom']} {u['Prenom']}"
                    t = get_upl_time()
                    
                    df_p = pd.read_csv(DB_P)
                    new_p = pd.DataFrame([{"Matricule": mat_id, "Identite": nom_c, "Classe": u['Classe'], "Date": t.strftime("%d/%m/%Y"), "Heure": t.strftime("%H:%M:%S")}])
                    pd.concat([df_p, new_p]).to_csv(DB_P, index=False)
                    
                    st.success(f"Bienvenue {u['Prenom']} ! Pointage validé.")
                    st.balloons()
                else:
                    st.error("Étudiant non répertorié.")
            st.markdown("</div>", unsafe_allow_html=True)

    elif nav == "📊 Calcul Bulletin":
        st.title("📊 Calculateur de Résultats")
        nb = st.number_input("Nombre de cours", 1, 15, 5)
        with st.form("bulletin_form"):
            notes, maxs = [], []
            for i in range(int(nb)):
                col = st.columns(2)
                notes.append(col[0].number_input(f"Note {i+1}", 0.0, 100.0, 10.0))
                maxs.append(col[1].number_input(f"Sur /", 1.0, 100.0, 20.0))
            if st.form_submit_button("VOIR LE POURCENTAGE"):
                p = (sum(notes)/sum(maxs)) * 100
                st.write(f"## {round(p, 2)}%")
                if p >= 80: st.success("EXCELLENT 🌟")
                elif p >= 50: st.info("RÉUSSI ✅")
                else: st.error("ÉCHEC ❌")

# ---------------------------------------------------------
# INTERFACE ADMIN (PROFESSIONNELLE)
# ---------------------------------------------------------
else:
    st.sidebar.title("💎 ADMIN PANEL")
    if st.sidebar.button("🚪 Déconnexion"):
        st.query_params.clear()
        st.rerun()

    menu_adm = st.radio("ACTIONS", ["📈 Statistiques", "👥 Scolarité", "⚙️ Maintenance"], horizontal=True)

    if menu_adm == "📈 Statistiques":
        df_p = pd.read_csv(DB_P)
        df_e = pd.read_csv(DB_E)
        
        # Dashboard Cards
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-card'><h3>Inscrits</h3><h1>{len(df_e)}</h1></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><h3>Présents</h3><h1>{len(df_p)}</h1></div>", unsafe_allow_html=True)
        taux = (len(df_p)/len(df_e)*100) if len(df_e)>0 else 0
        m3.markdown(f"<div class='metric-card'><h3>Taux</h3><h1>{round(taux,1)}%</h1></div>", unsafe_allow_html=True)

        if not df_p.empty:
            c_graph, c_table = st.columns([1, 1.5])
            with c_graph:
                st.write("#### Répartition par Classe")
                fig, ax = plt.subplots(facecolor='#161B22')
                counts = df_p['Classe'].value_counts()
                ax.pie(counts, labels=counts.index, autopct='%1.1f%%', textprops={'color':"w"})
                st.pyplot(fig)
            with c_table:
                st.write("#### Derniers Pointages")
                st.dataframe(df_p.tail(10), use_container_width=True)

    elif menu_adm == "👥 Scolarité":
        st.subheader("Ajouter un Étudiant")
        with st.form("add"):
            c1, c2, c3 = st.columns(3)
            m = c1.text_input("Matricule")
            n = c2.text_input("Nom")
            cl = c3.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA", "L1 INFO"])
            if st.form_submit_button("Enregistrer"):
                df = pd.read_csv(DB_E)
                pd.concat([df, pd.DataFrame([{"Matricule":m, "Nom":n, "Postnom":"", "Prenom":"", "Classe":cl}])]).to_csv(DB_E, index=False)
                st.success("Ajouté !")
        
        st.divider()
        st.write("### Base de données complète")
        df_edit = pd.read_csv(DB_E)
        st.dataframe(df_edit, use_container_width=True)

    elif menu_adm == "⚙️ Maintenance":
        st.subheader("⚠️ Zone de Danger")
        if st.button("NETTOYER LE REGISTRE DES PRÉSENCES"):
            pd.DataFrame(columns=["Matricule", "Identite", "Classe", "Date", "Heure"]).to_csv(DB_P, index=False)
            st.warning("Registre vidé.")
