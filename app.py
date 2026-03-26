import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
from io import BytesIO
import time

# --- CONFIGURATION DU DESIGN (PREMIUM UPL) ---
st.set_page_config(page_title="EduTracer UPL Pro", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* Fond et Police Globale */
    .main { background-color: #f4f7f9; font-family: 'Roboto', sans-serif; }
    
    /* Boutons Modernes avec Dégradé */
    .stButton>button { width: 100%; border-radius: 25px; background: linear-gradient(135deg, #004e92, #000428); color: white; font-weight: bold; border: none; height: 3.5em; transition: 0.3s; box-shadow: 0px 4px 10px rgba(0,0,0,0.2); }
    .stButton>button:hover { transform: scale(1.03); box-shadow: 0px 6px 20px rgba(0,0,0,0.3); }
    
    /* Cartes d'Information style "Card" */
    .card-pro { background-color: white; padding: 25px; border-radius: 15px; box-shadow: 0px 10px 25px rgba(0,0,0,0.05); border-top: 8px solid #004e92; text-align: center; margin-bottom: 20px; }
    
    /* Styles des Mentions pour le Bulletin */
    .mention-box { padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 22px; margin-top: 20px; border: 2px solid; }
    .elite { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
    .distinction { background-color: #e2f0d9; color: #1e4d1e; border-color: #c9e2b3; }
    .satisfaction { background-color: #fff3cd; color: #856404; border-color: #ffeeba; }
    .echec { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DES DONNÉES EN MÉMOIRE (SESSION) ---
# Dans un projet réel, ces données seraient chargées depuis ton Google Sheets
if 'registre_presences_ia' not in st.session_state:
    st.session_state.registre_presences_ia = []

# Base de données simulée des élèves inscrits
if 'db_eleves_upl' not in st.session_state:
    st.session_state.db_eleves_upl = pd.DataFrame([
        {"Matricule": "2025023061", "Nom": "BANZE", "Postnom": "KANDOLO", "Prenom": "Julien", "Classe": "Bac 1 IA"},
        {"Matricule": "2025000123", "Nom": "KABAMBA", "Postnom": "ILUNGA", "Prenom": "Marc", "Classe": "Bac 1 IA"},
        {"Matricule": "2025000999", "Nom": "MWENZE", "Postnom": "KASONG", "Prenom": "Sarah", "Classe": "Bac 1 IA"}
    ])

# --- GESTION DE L'ACCÈS ADMIN CACHÉ ---
# L'interface admin n'est visible que si l'URL se termine par ?admin=julien
# Utilisation de la nouvelle méthode officielle st.query_params
params = st.query_params
is_admin = params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE ÉLÈVE (PORTAIL PUBLIC)
# ---------------------------------------------------------
if not is_admin:
    # Navigation Côté Client
    st.sidebar.markdown("<h2 style='text-align: center; color: #004e92;'>💎 Portail UPL</h2>", unsafe_allow_html=True)
    choix_client = st.sidebar.radio("Navigation :", ["📍 Pointage Présence", "📊 Calcul Bulletin"])
    
    # --- PAGE 1 : POINTAGE PRÉSENCE (VISAGE) ---
    if choix_client == "📍 Pointage Présence":
        st.markdown("<h1 style='text-align: center; color: #004e92;'>🛡️ EduTracer : Pointage Facial Biométrique</h1>", unsafe_allow_html=True)
        st.write(f"<p style='text-align: center;'>Lubumbashi, le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>", unsafe_allow_html=True)
        
        col_cam, col_identite = st.columns([1, 1.2])
        
        with col_cam:
            st.markdown("<div class='card-pro'>", unsafe_allow_html=True)
            st.subheader("📸 Reconnaissance Faciale")
            st.camera_input("Scanner le visage")
            
            st.info("Placez votre visage devant la caméra pour l'identification...")
            
            # Champ de simulation (à remplacer par un modèle IA de reco faciale)
            face_id_sim = st.text_input("Simulation Identité Visuelle (Matricule) :", placeholder="Saisir pour tester le scan...")
            btn_confirmer = st.button("CONFIRMER LA PRÉSENCE")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_identite:
            if btn_confirmer and face_id_sim:
                # Recherche de l'élève dans la base de données
                resultat_scan = st.session_state.db_eleves_upl[st.session_state.db_eleves_upl['Matricule'] == face_id_sim]
                
                if not resultat_scan.empty:
                    eleve_scanne = resultat_scan.iloc[0]
                    maintenant = datetime.now()
                    
                    # AFFICHAGE DE L'IDENTITÉ COMPLÈTE
                    st.markdown(f"""
                    <div class='card-pro' style='border-top-color: #28a745;'>
                        <h2 style='color: #28a745;'>✅ IDENTITÉ CONFIRMÉE</h2>
                        <hr>
                        <p style='font-size: 20px;'><b>Étudiant :</b> {eleve_scanne['Nom']} {eleve_scanne['Postnom']} {eleve_scanne['Prenom']}</p>
                        <p style='font-size: 18px;'><b>Classe :</b> {eleve_scanne['Classe']}</p>
                        <p style='font-size: 18px;'><b>Matricule ID :</b> {eleve_scanne['Matricule']}</p>
                        <div style='background-color: #e9ecef; padding: 10px; border-radius: 10px; font-weight: bold;'>
                            Pointage réussi à {maintenant.strftime('%H:%M:%S')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # STOCKAGE SILENCIEUX DANS LA BASE DE DONNÉES CÔTÉ ADMIN
                    st.session_state.registre_presences_ia.append({
                        "Matricule": eleve_scanne['Matricule'],
                        "Identité": f"{eleve_scanne['Nom']} {eleve_scanne['Prenom']}",
                        "Classe": eleve_scanne['Classe'],
                        "Date": maintenant.strftime("%d/%m/%Y"),
                        "Heure": maintenant.strftime("%H:%M:%S"),
                        "Méthode": "Reconnaissance Faciale"
                    })
                    st.toast("Synchronisation avec le serveur central de l'UPL...")
                    st.balloons()
                else:
                    st.error("❌ Erreur : Visage non reconnu ou étudiant non inscrit.")
    
    # --- PAGE 2 : CALCUL BULLETIN (DYNAMIQUE) ---
    elif choix_client == "📊 Calcul Bulletin":
        st.markdown("<h1 style='text-align: center; color: #004e92;'>🧮 Calculateur de Bulletin Académique</h1>", unsafe_allow_html=True)
        st.write("Outil d'autoevaluation des résultats pour les étudiants.")
        
        with st.container():
            st.markdown("<div class='card-pro'>", unsafe_allow_html=True)
            # Étape 1 : Nombre de cours
            nombre_matiere = st.number_input("Nombre de matières à évaluer :", min_value=1, max_value=15, value=5)
            st.markdown("---")
            
            # Étape 2 : Boucle dynamique pour les notes
            with st.form("formulaire_bulletin_ia"):
                st.write("Saisie des notes par matière :")
                notes_obtenues = []
                max_matiere = []
                
                cols_form = st.columns(3)
                # La boucle Python génère les champs selon le nombre entré
                for i in range(int(nombre_matiere)):
                    with cols_form[i % 3]:
                        note_matiere = st.number_input(f"Matière {i+1}", min_value=0.0, max_value=100.0, value=10.0, key=f"note_cours_{i}")
                        max_cours = st.number_input(f"Maximum /10, /20, /50, /100", min_value=1.0, max_value=100.0, value=20.0, key=f"max_cours_{i}")
                        notes_obtenues.append(note_matiere)
                        max_matiere.append(max_cours)
                
                st.markdown("---")
                calculer_btn = st.form_submit_button("CALCULER LE RÉSULTAT FINAL")
                
                # Étape 3 : Calculs et Affichage des Résultats
                if calculer_btn:
                    total_points_obtenus = sum(notes_obtenues)
                    total_points_max = sum(max_matiere)
                    resultat_pourcentage = (total_points_obtenus / total_points_max) * 100
                    
                    st.divider()
                    st.metric("POURCENTAGE TOTAL", f"{round(resultat_pourcentage, 2)}%", f"{total_obtenu}/{total_global}")
                    
                    # LOGIQUE DES MENTIONS (IF/ELIF)
                    if resultat_pourcentage >= 80:
                        st.markdown("<div class='mention-box elite'>MENTION : EXCELLENT (ÉLITE) 🌟</div>", unsafe_allow_html=True)
                    elif resultat_pourcentage >= 70:
                        st.markdown("<div class='mention-box distinction'>MENTION : DISTINCTION 🎓</div>", unsafe_allow_html=True)
                    elif resultat_pourcentage >= 50:
                        st.markdown("<div class='mention-box satisfaction'>MENTION : SATISFACTION ✅</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='mention-box echec'>MENTION : AJOURNÉ ❌</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# INTERFACE ADMIN (CACHÉE VIA ?admin=julien)
# ---------------------------------------------------------
else:
    st.sidebar.markdown(f"### 👑 Admin Session : Julien")
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100) # Icône Admin
    mode_admin = st.sidebar.radio("Outils de Gestion :", ["📊 Registre Présences", "👥 Gestion Élèves", "🪪 Générateur de Cartes"])

    # --- SOUS-PAGE 1 : REGISTRE DES PRÉSENCES ---
    if mode_admin == "📊 Registre Présences":
        st.title("📈 Journal Biométrique en Temps Réel")
        st.write("Liste de tous les étudiants ayant pointé via reconnaissance faciale.")
        
        if st.session_state.registre_presences_ia:
            df_presences = pd.DataFrame(st.session_state.registre_presences_ia)
            # Affichage du tableau de données complet
            st.dataframe(df_presences, use_container_width=True)
            
            # Bouton de téléchargement pour le rapport final
            csv_rapport = df_presences.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger le rapport (CSV)", csv_rapport, "registre_upl_ia.csv", "text/csv")
        else:
            st.info("Aucun pointage enregistré pour le moment.")

    # --- SOUS-PAGE 2 : GESTION ÉLÈVES ---
    elif mode_admin == "👥 Gestion Élèves":
        st.title("📚 Liste des Étudiants Inscrits à l'UPL")
        # Affiche la base de données simulée
        st.dataframe(st.session_state.db_eleves_upl, use_container_width=True)
        st.write(f"Total des étudiants répertoriés : {len(st.session_state.db_eleves_upl)}")

    # --- SOUS-PAGE 3 : GÉNÉRATEUR DE CARTES ---
    elif mode_admin == "🪪 Générateur de Cartes":
        st.title("🖨️ Générateur de Cartes d'Étudiant Sécurisées")
        c1, c2 = st.columns(2)
        m_carte = c1.text_input("Matricule à encoder")
        n_carte = c2.text_input("Nom de l'étudiant")
        
        if st.button("Générer le QR Code de Sécurité"):
            if m_carte and n_carte:
                qr_sec = qrcode.make(f"UPL-SECURE-{m_carte}")
                buf_carte = BytesIO()
                qr_sec.save(buf_carte, format="PNG")
                st.image(buf_carte, width=200, caption=f"QR de Sécurité pour {n_carte}")
                st.success("QR Code généré. Prêt pour l'impression de la carte.")
            else:
                st.error("Veuillez remplir le matricule et le nom.")
