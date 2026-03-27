import streamlit as st
from supabase import create_client, Client
import time

# --- CONFIGURATION SUPABASE ---
URL_SUPABASE = "https://tqlrzrbskptsnazawycq.supabase.co"
CLE_SUPABASE = "sb_publishable_LMk35Kkv_gZVGwpkX-aHPA_H1XxRHKp"
supabase: Client = create_client(URL_SUPABASE, CLE_SUPABASE)

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="EduTracer Pro UPL", layout="wide")

# --- STYLE CSS POUR UN LOOK PROFESSIONNEL ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1E3A8A; color: white; font-weight: bold; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .main { background-color: #F3F4F6; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE DE SECURITE ---
query_params = st.query_params
is_admin = query_params.get("admin") == "julien"

# --- SIDEBAR (NAVIGATION CACHÉE) ---
st.sidebar.title("🏫 Système UPL")
if is_admin:
    st.sidebar.success("👑 SESSION PROPRIÉTAIRE")
    menu = st.sidebar.radio("Navigation Admin", ["Tableau de Bord", "Enrôlement Biométrique", "Contrôle de Caisse", "Base de Données"])
else:
    st.sidebar.info("📌 Portail Public")
    menu = st.sidebar.radio("Navigation", ["Pointage Empreinte", "Espace Étudiant"])

# --- 1. MODULE POINTAGE (PUBLIC) ---
if menu == "Pointage Empreinte":
    st.title("🖐️ Terminal Biométrique de Présence")
    st.write("Veuillez poser votre doigt sur le capteur du smartphone ou du lecteur USB.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("🔥 ACTIVER LE CAPTEUR D'EMPREINTE"):
            with st.spinner("Lecture des données biométriques..."):
                time.sleep(2) # Temps de scan
                
                # Simulation de l'ID reçu par le capteur
                # En HTTPS réel, on appelle ici window.navigator.credentials.get()
                scanned_id = "BIO_99" 
                
                # Vérification croisée (Empreinte + Finance + Présence)
                res = supabase.table("eleves").select("*").eq("empreinte_id", scanned_id).execute()
                
                if res.data:
                    user = res.data[0]
                    if user['est_en_regle']:
                        # Enregistrement présence
                        supabase.table("presences").insert({
                            "eleve_matricule": user['matricule'],
                            "session_type": "Matin"
                        }).execute()
                        st.success(f"✅ PRÉSENCE VALIDÉE : {user['nom']} {user['postnom']} ({user['classe_id']})")
                        st.balloons()
                    else:
                        st.error(f"❌ ACCÈS REFUSÉ : {user['nom']}, frais scolaires non soldés.")
                else:
                    st.warning("⚠️ Empreinte non reconnue. Contactez l'administration.")

# --- 2. MODULE ENRÔLEMENT (ADMIN SEULEMENT) ---
elif menu == "Enrôlement Biométrique" and is_admin:
    st.title("📝 Enrôlement des nouveaux étudiants")
    
    with st.form("inscription"):
        c1, c2 = st.columns(2)
        with c1:
            nom = st.text_input("Nom de famille")
            mat = st.text_input("Matricule Officiel")
        with c2:
            postnom = st.text_input("Postnom")
            promo = st.selectbox("Promotion", ["Bac 1 IA", "Bac 2 IA", "L2 Info"])
        
        st.write("---")
        st.markdown("### 🖐️ Liaison Empreinte Digitale")
        st.info("L'élève doit être présent pour lier son identité physique au matricule.")
        
        if st.form_submit_button("Lier l'empreinte et Sauvegarder"):
            # Simulation génération clé cryptographique
            new_bio_id = f"BIO_{int(time.time())}" 
            
            try:
                supabase.table("eleves").insert({
                    "matricule": mat, "nom": nom, "postnom": postnom,
                    "classe_id": promo, "empreinte_id": new_bio_id
                }).execute()
                st.success(f"✅ Enrôlement réussi. ID Biométrique : {new_bio_id}")
            except:
                st.error("Erreur : Ce matricule existe déjà.")

# --- 3. MODULE CAISSE (ADMIN SEULEMENT) ---
elif menu == "Contrôle de Caisse" and is_admin:
    st.title("💰 Gestion de la Solvabilité")
    search = st.text_input("Entrez le matricule pour valider un paiement")
    
    if search:
        res = supabase.table("eleves").select("*").eq("matricule", search).execute()
        if res.data:
            el = res.data[0]
            st.write(f"Élève : **{el['nom']} {el['postnom']}**")
            current = "✅ PAYÉ" if el['est_en_regle'] else "❌ DETTE"
            st.info(f"Statut financier : {current}")
            
            if st.button("Valider le paiement (Mettre en règle)"):
                supabase.table("eleves").update({"est_en_regle": True}).eq("matricule", search).execute()
                st.success("Paiement enregistré ! L'élève peut désormais pointer.")
        else:
            st.error("Matricule inconnu.")

# --- 4. MODULE ETUDIANT (PUBLIC) ---
elif menu == "Espace Étudiant":
    st.title("📊 Mon Tableau de Bord")
    m_check = st.text_input("Matricule :")
    if m_check:
        res = supabase.table("eleves").select("*").eq("matricule", m_check).execute()
        if res.data:
            u = res.data[0]
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Statut Financier", "SOLVABLE" if u['est_en_regle'] else "NON SOLVABLE")
            with c2:
                pres = supabase.table("presences").select("*", count="exact").eq("eleve_matricule", m_check).execute()
                st.metric("Taux de présence", f"{pres.count} jours")
        else:
            st.warning("Aucun dossier trouvé.")
