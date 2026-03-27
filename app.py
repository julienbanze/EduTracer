import streamlit as st
from supabase import create_client, Client
import time
from datetime import datetime

# --- CONFIGURATION (A REMPLIR AVEC TES CLES) ---
URL_SUPABASE = "https://tqlrzrbskptsnazawycq.supabase.co"
KEY_SUPABASE = "sb_publishable_LMk35Kkv_gZVGwpkX-aHPA_H1XxRHKp"
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="EduTracer Pro", layout="wide", page_icon="🏫")

# --- DESIGN "SCHOOL ELITE" ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    div.stButton > button:first-child {
        height: 80px; width: 100%; border-radius: 15px;
        font-size: 20px; font-weight: 600; color: #1E3A8A;
        background-color: white; border: 2px solid #1E3A8A;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #1E3A8A; color: white; transform: translateY(-3px);
    }
    .status-box { padding: 20px; border-radius: 15px; background: white; border-left: 5px solid #1E3A8A; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ET ROLES ---
if "role" not in st.session_state:
    st.session_state.role = "Portail"

def changer_role(nouveau_role):
    st.session_state.role = nouveau_role

# Check Admin Secret
is_admin = st.query_params.get("admin") == "julien"

# ==========================================
# PAGE 1 : LE PORTAIL DE CHOIX (CLIENT)
# ==========================================
if st.session_state.role == "Portail":
    st.title("🏫 EduTracer - Système de Gestion Scolaire")
    st.write("### Sélectionnez votre espace de travail")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("### 👨‍🏫 ENSEIGNANT\nPointage & Présences")
        st.button("Accéder à l'espace Prof", on_click=changer_role, args=("Prof",))
    with col2:
        st.success("### 💰 COMPTABILITÉ\nFrais & Paiements")
        st.button("Accéder à la Caisse", on_click=changer_role, args=("Caisse",))
    with col3:
        st.warning("### 👶 ÉLÈVE / PARENT\nSuivi Dossier")
        st.button("Consulter mon Dossier", on_click=changer_role, args=("Eleve",))

    if is_admin:
        st.divider()
        st.button("⚙️ ADMINISTRATION (PROPRIÉTAIRE)", on_click=changer_role, args=("Admin",))

# ==========================================
# PAGE 2 : ESPACE PROFESSEUR (POINTAGE BIOMÉTRIQUE)
# ==========================================
elif st.session_state.role == "Prof":
    st.sidebar.button("⬅️ Retour au Portail", on_click=changer_role, args=("Portail",))
    st.title("🖐️ Terminal de Pointage")
    
    cl_select = st.selectbox("Sélectionnez la classe actuelle", ["1ère Primaire", "6ème Secondaire"])
    
    if st.button("🔴 ACTIVER LE CAPTEUR D'EMPREINTE"):
        with st.spinner("En attente du doigt sur le capteur..."):
            time.sleep(2) # Simulation lecture Android
            
            # Simulation d'un ID lu par le téléphone
            id_scanne = "BIO_TEST_001" 
            
            # Requête Supabase : On vérifie l'identité et la finance
            res = supabase.table("eleves").select("*").eq("empreinte_id", id_scanne).execute()
            
            if res.data:
                eleve = res.data[0]
                if eleve['est_en_regle']:
                    st.success(f"✅ PRÉSENCE VALIDÉE : {eleve['nom']} {eleve['postnom']}")
                    # Insertion avec les colonnes SQL corrigées
                    supabase.table("presences").insert({
                        "eleve_matricule": eleve['matricule'],
                        "cours_ou_activite": "Cours du Matin"
                    }).execute()
                else:
                    st.error(f"❌ BLOCAGE FINANCIER : {eleve['nom']}, frais non payés.")
            else:
                st.error("⚠️ Empreinte non reconnue. Contactez l'administration.")

# ==========================================
# PAGE 3 : ESPACE ADMIN (SURVEILLANCE TOTALE)
# ==========================================
elif st.session_state.role == "Admin":
    st.sidebar.button("⬅️ Quitter Admin", on_click=changer_role, args=("Portail",))
    st.title("⚙️ Surveillance Totale")
    
    t1, t2, t3 = st.tabs(["📊 Flux de Présence", "👤 Enrôlement", "📈 Statistiques"])
    
    with t1:
        st.subheader("Journal des activités (Derniers scans)")
        # Jointure pour voir le NOM au lieu du simple matricule
        logs = supabase.table("presences").select("id, date_pointage, heure_pointage, eleve_matricule, eleves(nom, postnom)").order("id", desc=True).limit(15).execute()
        if logs.data:
            st.table(logs.data)
        else:
            st.info("Aucun mouvement enregistré aujourd'hui.")

    with t2:
        st.subheader("Inscrire un nouvel élève")
        with st.form("inscription_form"):
            colA, colB = st.columns(2)
            with colA:
                nom = st.text_input("Nom de l'enfant")
                mat = st.text_input("Matricule Unique")
            with colB:
                post = st.text_input("Postnom")
                cl = st.text_input("Classe (ex: 4ème A)")
            
            if st.form_submit_button("Lier l'Empreinte & Sauvegarder"):
                # On génère un ID unique pour l'empreinte
                new_bio_id = f"BIO_{int(time.time())}"
                supabase.table("eleves").insert({
                    "matricule": mat, "nom": nom, "postnom": post,
                    "classe_id": cl, "empreinte_id": new_bio_id
                }).execute()
                st.success(f"✅ Enregistré avec succès ! ID Empreinte : {new_bio_id}")
