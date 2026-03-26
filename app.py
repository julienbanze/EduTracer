import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
from io import BytesIO
import time

# --- CONFIGURATION DU DESIGN ---
st.set_page_config(page_title="EduTracer UPL - Biométrie", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { width: 100%; border-radius: 25px; background: linear-gradient(135deg, #004e92, #000428); color: white; font-weight: bold; border: none; height: 3.5em; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0px 4px 15px rgba(0,0,0,0.3); }
    .card-eleve { background-color: white; padding: 30px; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.1); border-top: 8px solid #004e92; text-align: center; }
    .mention-box { padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 22px; margin-top: 20px; }
    .elite { background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
    .echec { background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DES DONNÉES (SESSION) ---
if 'db_presences' not in st.session_state:
    st.session_state.db_presences = []

# Simulation d'une base de données d'élèves inscrits à l'UPL
if 'liste_inscrits' not in st.session_state:
    st.session_state.liste_inscrits = pd.DataFrame([
        {"Matricule": "2025023061", "Nom": "BANZE", "Postnom": "KANDOLO", "Prenom": "Julien", "Classe": "Bac 1 IA"},
        {"Matricule": "2025000123", "Nom": "KABAMBA", "Postnom": "ILUNGA", "Prenom": "Marc", "Classe": "Bac 1 IA"}
    ])

# --- GESTION DE L'ACCÈS ADMIN ---
# L'interface admin n'est visible que si l'URL se termine par ?admin=julien
params = st.query_params
is_admin = params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE 1 : SCANNER D'EMPREINTE (PUBLIC)
# ---------------------------------------------------------
if not is_admin:
    st.markdown("<h1 style='text-align: center; color: #004e92;'>🛡️ EduTracer : Pointage Biométrique</h1>", unsafe_allow_html=True)
    st.write(f"<p style='text-align: center;'>Lubumbashi, le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.markdown("<div class='card-eleve'>", unsafe_allow_html=True)
        st.subheader("🧬 Lecteur d'Empreinte")
        # Icône illustrative du capteur
        st.image("https://cdn-icons-png.flaticon.com/512/2638/2638127.png", width=180)
        st.info("Posez votre doigt sur le capteur USB...")
        
        # Champ de simulation (à remplacer par un SDK de capteur en local)
        scan_id = st.text_input("Simulation Signal Biométrique (Matricule) :", placeholder="Scannez ici...")
        confirm = st.button("DÉTECTER L'EMPREINTE")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        if confirm and scan_id:
            # Recherche de l'élève
            result = st.session_state.liste_inscrits[st.session_state.liste_inscrits['Matricule'] == scan_id]
            
            if not result.empty:
                eleve = result.iloc[0]
                now = datetime.now()
                
                # AFFICHAGE DES IDENTITÉS
                st.markdown(f"""
                <div class='card-eleve'>
                    <h2 style='color: #28a745;'>✅ ACCÈS AUTORISÉ</h2>
                    <hr>
                    <p style='font-size: 20px;'><b>Étudiant :</b> {eleve['Nom']} {eleve['Postnom']} {eleve['Prenom']}</p>
                    <p style='font-size: 18px;'><b>Classe :</b> {eleve['Classe']}</p>
                    <p style='font-size: 18px;'><b>ID Biométrique :</b> {eleve['Matricule']}</p>
                    <div style='background-color: #e9ecef; padding: 10px; border-radius: 10px;'>
                        Pointage enregistré à {now.strftime('%H:%M:%S')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # STOCKAGE SILENCIEUX CÔTÉ ADMIN
                st.session_state.db_presences.append({
                    "Matricule": eleve['Matricule'],
                    "Identité": f"{eleve['Nom']} {eleve['Prenom']}",
                    "Date": now.strftime("%d/%m/%Y"),
                    "Heure": now.strftime("%H:%M:%S"),
                    "Méthode": "Empreinte Digitale"
                })
                st.balloons()
            else:
                st.error("❌ Empreinte non reconnue. Accès refusé.")

# ---------------------------------------------------------
# INTERFACE 2 : PANEL ADMINISTRATION (CACHÉ)
# ---------------------------------------------------------
else:
    st.sidebar.markdown("### 👑 Session : Julien")
    mode = st.sidebar.radio("Outils Admin :", ["📊 Registre des Présences", "🎓 Calculateur de Bulletin", "🪪 Gestion des Cartes"])

    # --- REGISTRE DES PRÉSENCES ---
    if mode == "📊 Registre des Présences":
        st.title("📈 Journal Biométrique en Temps Réel")
        if st.session_state.db_presences:
            df = pd.DataFrame(st.session_state.db_presences)
            st.dataframe(df, use_container_width=True)
            # Bouton de téléchargement
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger le rapport CSV", csv, "presences_upl.csv", "text/csv")
        else:
            st.info("Aucune présence enregistrée via empreinte aujourd'hui.")

    # --- CALCULATEUR DE BULLETIN DYNAMIQUE ---
    elif mode == "🎓 Calculateur de Bulletin":
        st.title("🧮 Calculateur de Résultats Global")
        
        with st.container():
            st.markdown("<div class='card-eleve'>", unsafe_allow_html=True)
            nb_cours = st.number_input("Nombre de matières à calculer :", 1, 15, 5)
            
            with st.form("bulletin_form"):
                st.write("Saisie des notes par matière :")
                notes = []
                max_notes = []
                
                cols = st.columns(3)
                for i in range(int(nb_cours)):
                    with cols[i % 3]:
                        n = st.number_input(f"Note Matière {i+1}", 0.0, 100.0, 10.0, key=f"n_{i}")
                        m = st.number_input(f"Max Matière {i+1}", 1.0, 100.0, 20.0, key=f"m_{i}")
                        notes.append(n)
                        max_notes.append(m)
                
                submit = st.form_submit_button("CALCULER LE RÉSULTAT FINAL")
                
                if submit:
                    total_obtenu = sum(notes)
                    total_max = sum(max_notes)
                    pourcentage = (total_obtenu / total_max) * 100
                    
                    st.divider()
                    st.metric("POURCENTAGE TOTAL", f"{round(pourcentage, 2)}%", f"{total_obtenu}/{total_max}")
                    
                    # Logique des mentions
                    if pourcentage >= 80:
                        st.markdown("<div class='mention-box elite'>MENTION : EXCELLENT (ÉLITE) 🌟</div>", unsafe_allow_html=True)
                    elif pourcentage >= 70:
                        st.markdown("<div class='mention-box elite'>MENTION : DISTINCTION 🎓</div>", unsafe_allow_html=True)
                    elif pourcentage >= 50:
                        st.markdown("<div class='mention-box elite' style='background-color:#fff3cd; color:#856404;'>MENTION : SATISFACTION ✅</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='mention-box echec'>MENTION : AJOURNÉ ❌</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- GESTION DES CARTES ---
    elif mode == "🪪 Gestion des Cartes":
        st.title("🖨️ Générateur de Cartes Sécurisées")
        c1, c2 = st.columns(2)
        m_c = c1.text_input("Matricule à encoder")
        n_c = c2.text_input("Nom de l'étudiant")
        
        if st.button("Générer QR de Sécurité"):
            qr = qrcode.make(f"UPL-BIO-{m_c}")
            buf = BytesIO()
            qr.save(buf, format="PNG")
            st.image(buf, width=200, caption=f"QR Code Biométrique pour {n_c}")
