import streamlit as st
from supabase import create_client, Client
import time
from datetime import datetime

# --- CONFIGURATION ---
URL = "https://tqlrzrbskptsnazawycq.supabase.co"
KEY = "sb_publishable_LMk35Kkv_gZVGwpkX-aHPA_H1XxRHKp"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="EduTracer OS - UPL", layout="wide")

# --- STYLE CSS (Interface Moderne) ---
st.markdown("""
    <style>
    .stButton>button { height: 4em; border-radius: 12px; font-weight: bold; font-size: 18px; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); background-color: #1E40AF; color: white; }
    .role-card { padding: 20px; border-radius: 15px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION ---
if "page" not in st.session_state:
    st.session_state.page = "Portail"

# --- SECURITÉ ADMIN URL ---
is_admin = st.query_params.get("admin") == "julien"

# --- FONCTION DE DECONNEXION ---
def logout():
    st.session_state.page = "Portail"
    st.rerun()

# ==========================================
# 1. LE PORTAIL DE CHOIX (ACCUEIL)
# ==========================================
if st.session_state.page == "Portail":
    st.title("🏛️ Université Protestante de Lubumbashi")
    st.subheader("Système de Gestion Biométrique - Choisissez votre espace")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="role-card"><h3>👨‍🏫 Enseignant / Prof</h3></div>', unsafe_allow_html=True)
        if st.button("Accéder (Cours & Présences)"):
            st.session_state.page = "Prof"
            st.rerun()

    with col2:
        st.markdown('<div class="role-card"><h3>🎓 Élève</h3></div>', unsafe_allow_html=True)
        if st.button("Accéder (Dossier & Notes)"):
            st.session_state.page = "Eleve"
            st.rerun()

    with col3:
        st.markdown('<div class="role-card"><h3>💰 Caissier</h3></div>', unsafe_allow_html=True)
        if st.button("Accéder (Paiements)"):
            st.session_state.page = "Caissier"
            st.rerun()

    if is_admin:
        st.divider()
        if st.button("🛠️ PANNEAU DE CONTRÔLE PROPRIÉTAIRE"):
            st.session_state.page = "Admin"
            st.rerun()

# ==========================================
# 2. ESPACE PROFESSEUR (POINTAGE)
# ==========================================
elif st.session_state.page == "Prof":
    st.sidebar.button("⬅️ Retour", on_click=logout)
    st.title("📑 Session de Cours")
    cours = st.text_input("Intitulé du cours (ex: Algorithmique)")
    
    if st.button("✋ Lancer le scan des présences"):
        st.info("Scanner actif. En attente du doigt de l'élève...")
        # Ici l'API WebAuthn Android s'active
        time.sleep(2)
        # Simulation d'un retour Android
        found_id = "BIO_99" 
        
        res = supabase.table("eleves").select("*").eq("empreinte_id", found_id).execute()
        if res.data:
            el = res.data[0]
            if el['est_en_regle']:
                st.success(f"✅ PRÉSENCE VALIDÉE : {el['nom']} {el['postnom']}")
                supabase.table("presences").insert({
                    "eleve_matricule": el['matricule'],
                    "cours": cours,
                    "date_heure": datetime.now().isoformat()
                }).execute()
            else:
                st.error(f"❌ BLOCAGE : {el['nom']} n'est pas en règle de paiement.")
        else:
            st.error("⚠️ Empreinte non reconnue. Contactez l'administration.")

# ==========================================
# 3. ESPACE ADMIN (SURVEILLANCE TOTALE)
# ==========================================
elif st.session_state.page == "Admin":
    st.sidebar.button("⬅️ Quitter Admin", on_click=logout)
    st.title("⚙️ Surveillance Totale du Système")
    
    t1, t2, t3 = st.tabs(["Flux en Direct", "Enrôlement Biométrique", "Statistiques"])
    
    with t1:
        st.subheader("📅 Journal des activités (Temps Réel)")
        # L'admin voit TOUT : date, heure, jour, action
        logs = supabase.table("presences").select("*").order("date_heure", desc=True).limit(20).execute()
        st.table(logs.data) # Affiche Date, Heure, Matricule, Cours

    with t2:
        st.subheader("🖐️ Nouvel Enrôlement")
        with st.form("new_user"):
            nom = st.text_input("Nom")
            mat = st.text_input("Matricule")
            if st.form_submit_button("Lier Empreinte & Sauvegarder"):
                # On génère l'ID Biométrique unique
                new_id = f"BIO_{int(time.time())}"
                supabase.table("eleves").insert({
                    "matricule": mat, "nom": nom, "empreinte_id": new_id
                }).execute()
                st.success(f"Inscrit avec l'ID Biométrique : {new_id}")

# ==========================================
# 4. ESPACE CAISSIER
# ==========================================
elif st.session_state.page == "Caissier":
    st.sidebar.button("⬅️ Retour", on_click=logout)
    st.title("💸 Gestion de la Caisse")
    mat_caisse = st.text_input("Matricule de l'élève")
    if mat_caisse:
        if st.button("Valider Paiement Minerval"):
            supabase.table("eleves").update({"est_en_regle": True}).eq("matricule", mat_caisse).execute()
            st.success("Paiement enregistré !")
