import streamlit as st
from supabase import create_client, Client
import time

# --- 1. CONFIGURATION SUPABASE ---
# Remplace par tes vraies clés de ton projet Supabase
URL_SUPABASE = "https://tqlrzrbskptsnazawycq.supabase.co"
CLE_SUPABASE = "sb_publishable_LMk35Kkv_gZVGwpkX-aHPA_H1XxRHKp"
supabase: Client = create_client(URL_SUPABASE, CLE_SUPABASE)

# --- 2. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="EduTracer Biometric Pro", layout="wide")

# Initialisation des états de session
if "role" not in st.session_state:
    st.session_state.role = "Public"
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

# --- 3. CODES D'ACCÈS AGENTS ---
CODES_ACCES = {
    "Scanner": "1111",
    "Finance": "3333",
}

# --- 4. NAVIGATION LATERALE ---
st.sidebar.title("🏢 EduTracer UPL")
if st.session_state.role != "Public":
    if st.sidebar.button("🔴 Déconnexion"):
        st.session_state.role = "Public"
        st.rerun()

# Logique Admin cachée via URL (?admin=julien)
query_params = st.query_params
if query_params.get("admin") == "julien":
    st.sidebar.success("👑 Mode Propriétaire Détecté")
    if st.sidebar.button("Accéder à l'Administration"):
        st.session_state.role = "Admin"

# --- 5. LOGIQUE DES MODULES ---

# --- A. ACCUEIL (PUBLIC) ---
if st.session_state.role == "Public":
    st.title("🚀 Portail Scolaire Biométrique")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("📖 **Espace Élève**")
        if st.button("Consulter mon Taux de Présence"):
            st.session_state.role = "Eleve"
            st.rerun()

    with col2:
        st.warning("🔐 **Espace Personnel**")
        tache = st.selectbox("Mission :", ["Scanner (Pointage)", "Finance (Paiements)"])
        code = st.text_input("Code d'accès :", type="password")
        if st.button("Ouvrir la session"):
            if tache == "Scanner (Pointage)" and code == CODES_ACCES["Scanner"]:
                st.session_state.role = "Agent_Scanner"
                st.rerun()
            elif tache == "Finance (Paiements)" and code == CODES_ACCES["Finance"]:
                st.session_state.role = "Agent_Finance"
                st.rerun()
            else:
                st.error("Accès refusé.")

# --- B. MODULE ADMIN (ENRÔLEMENT BIOMÉTRIQUE) ---
elif st.session_state.role == "Admin":
    st.title("⚙️ Panneau de Contrôle Admin")
    tab1, tab2 = st.tabs(["Nouvel Enrôlement", "Gestion des Classes"])
    
    with tab1:
        st.subheader("Enregistrer un nouvel élève et son empreinte")
        res_classes = supabase.table("classes").select("nom_classe").execute()
        liste_cl = [c['nom_classe'] for c in res_classes.data]
        
        with st.form("enrolement_form"):
            mat = st.text_input("Matricule Unique")
            nom = st.text_input("Nom & Postnom")
            cl = st.selectbox("Classe", liste_cl)
            st.write("---")
            st.info("Le capteur d'empreinte s'activera après validation.")
            
            if st.form_submit_button("Valider & Lier l'Empreinte"):
                # Simulation de l'appel au capteur du téléphone/PC
                # En mode réel : on utilise une API JS WebAuthn ici
                biometric_id = f"BIO_SIG_{mat}_{int(time.time())}" 
                
                try:
                    supabase.table("eleves").insert({
                        "matricule": mat, "nom": nom, 
                        "classe_id": cl, "empreinte_id": biometric_id
                    }).execute()
                    st.success(f"✅ Élève {nom} enregistré avec l'empreinte {biometric_id}")
                except:
                    st.error("Erreur : Matricule déjà existant.")

# --- C. MODULE SCANNER (POINTAGE QUOTIDIEN) ---
elif st.session_state.role == "Agent_Scanner":
    st.title("🖐️ Pointage par Empreinte Digitale")
    st.write("Posez votre doigt sur le capteur pour valider votre présence.")
    
    if st.button("🔥 DÉMARRER LE SCAN BIOMÉTRIQUE"):
        with st.spinner("Lecture de l'empreinte..."):
            time.sleep(2) # Simulation du temps de lecture
            
            # Simulation d'une empreinte reconnue (ID qui viendrait du capteur)
            test_bio_id = "BIO_SIG_2026-UPL-001" 
            
            # Vérification dans Supabase
            res = supabase.table("eleves").select("*").eq("empreinte_id", test_bio_id).execute()
            
            if res.data:
                user = res.data[0]
                # Vérifier si en règle de paiement
                if user['est_en_regle']:
                    st.success(f"✅ PRÉSENCE VALIDÉE : {user['nom']} ({user['classe_id']})")
                    # Enregistrement dans la table des présences
                    supabase.table("presences").insert({
                        "eleve_matricule": user['matricule'],
                        "session_type": "Matin"
                    }).execute()
                else:
                    st.error(f"⚠️ {user['nom']}, vous n'êtes pas en règle de paiement. Direction Finance.")
            else:
                st.error("❌ Empreinte Inconnue. Veuillez voir l'Admin.")

# --- D. MODULE ÉLÈVE (CONSULTATION) ---
elif st.session_state.role == "Eleve":
    st.title("📊 Mon Suivi Scolaire")
    m_check = st.text_input("Entrez votre matricule :")
    if m_check:
        res = supabase.table("eleves").select("*").eq("matricule", m_check).execute()
        if res.data:
            u = res.data[0]
            st.write(f"Bonjour **{u['nom']}**, voici votre état :")
            st.metric("Statut Financier", "EN RÈGLE" if u['est_en_regle'] else "NON RÉGLÉ")
            
            # Récupérer le nombre de présences
            p = supabase.table("presences").select("*", count="exact").eq("eleve_matricule", m_check).execute()
            st.metric("Nombre de présences ce mois", p.count)
        else:
            st.warning("Matricule non trouvé.")
