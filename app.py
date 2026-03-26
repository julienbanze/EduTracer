import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
from io import BytesIO
from PIL import Image

# --- CONFIGURATION DESIGN ---
st.set_page_config(page_title="EduTracer UPL Pro", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 12px; background: #004e92; color: white; font-weight: bold; border: none; height: 3em; }
    .card-pro { background-color: white; padding: 25px; border-radius: 15px; box-shadow: 0px 8px 20px rgba(0,0,0,0.1); border-left: 10px solid #004e92; }
    .id-card { border: 2px solid #333; border-radius: 10px; padding: 20px; background: #fff; width: 400px; margin: auto; font-family: sans-serif; }
    .header-upl { background: #004e92; color: white; padding: 10px; text-align: center; border-radius: 5px 5px 0 0; margin: -20px -20px 20px -20px; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DES BASES DE DONNÉES ---
if 'db_presences' not in st.session_state:
    st.session_state.db_presences = []

# --- SÉCURITÉ ADMIN ---
is_admin = st.query_params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE 1 : SCANNER QR (PUBLIC / ÉLÈVE)
# ---------------------------------------------------------
if not is_admin:
    st.markdown("<h1 style='text-align: center;'>🎓 UPL : Pointage par QR Code</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.markdown("<div class='card-pro'>", unsafe_allow_html=True)
        st.subheader("📷 Scanner de Carte")
        img_file = st.camera_input("Présentez votre QR Code devant la caméra")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.subheader("📝 Validation Manuelle")
        # On simule le contenu du QR Code par une saisie pour ta démo
        qr_content = st.text_input("Contenu du Scan (Nom-Postnom-Matricule) :", placeholder="Ex: BANZE-KANDOLO-2025")
        
        if st.button("VALIDER LA PRÉSENCE"):
            if qr_content:
                # On sépare les infos reçues du QR (format: Nom|Postnom|Prenom|Classe|Matricule)
                try:
                    infos = qr_content.split("|")
                    nom, pnom, pren, classe, mat = infos[0], infos[1], infos[2], infos[3], infos[4]
                    
                    now = datetime.now()
                    st.markdown(f"""
                    <div class='card-pro' style='border-left-color: #28a745;'>
                        <h3 style='color: #28a745;'>✅ ÉTUDIANT IDENTIFIÉ</h3>
                        <p><b>Nom Complet :</b> {nom} {pnom} {pren}</p>
                        <p><b>Classe :</b> {classe}</p>
                        <p><b>Matricule :</b> {mat}</p>
                        <p style='color: gray; font-size: 12px;'>Enregistré à {now.strftime('%H:%M:%S')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Stockage côté Admin
                    st.session_state.db_presences.append({
                        "Matricule": mat, "Nom": nom, "Postnom": pnom, "Prenom": pren,
                        "Classe": classe, "Date": now.strftime("%d/%m/%Y"), "Heure": now.strftime("%H:%M")
                    })
                    st.balloons()
                except:
                    st.error("❌ Format de QR Code invalide pour l'UPL.")
            else:
                st.warning("Veuillez scanner ou saisir les informations.")

# ---------------------------------------------------------
# INTERFACE 2 : PANEL ADMIN (CACHÉ)
# ---------------------------------------------------------
else:
    st.sidebar.title("💎 Admin : Julien")
    choix = st.sidebar.radio("Outils :", ["🪪 Générateur de Cartes", "📊 Suivi par Classe", "🎓 Calculateur de Résultats"])

    # 1. GÉNÉRATEUR DE CARTES COMPLET
    if choix == "🪪 Générateur de Cartes":
        st.title("🛠️ Création de Carte d'Étudiant")
        with st.form("form_card"):
            c1, c2 = st.columns(2)
            mat = c1.text_input("Matricule")
            nom = c2.text_input("Nom")
            postnom = c1.text_input("Postnom")
            prenom = c2.text_input("Prénom")
            classe = st.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA", "L1 INFO", "L2 INFO"])
            
            if st.form_submit_button("GÉNÉRER LA CARTE OFFICIELLE"):
                # On crée la chaîne de texte pour le QR
                data_for_qr = f"{nom}|{postnom}|{prenom}|{classe}|{mat}"
                
                qr = qrcode.make(data_for_qr)
                buf = BytesIO()
                qr.save(buf, format="PNG")
                
                st.divider()
                # Design de la carte à l'écran
                st.markdown(f"""
                <div class="id-card">
                    <div class="header-upl">UNIVERSITÉ PROTESTANTE DE LUBUMBASHI</div>
                    <div style="display: flex; gap: 15px;">
                        <div style="flex: 1;">
                            <p style="font-size: 12px; margin: 0;">NOM: <b>{nom}</b></p>
                            <p style="font-size: 12px; margin: 5px 0;">POSTNOM: <b>{postnom}</b></p>
                            <p style="font-size: 12px; margin: 5px 0;">PRENOM: <b>{prenom}</b></p>
                            <p style="font-size: 12px; margin: 5px 0;">CLASSE: <b>{classe}</b></p>
                            <p style="font-size: 14px; margin: 10px 0; color: #004e92;"><b>ID: {mat}</b></p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.image(buf, width=150, caption="Scan me to Check-in")

    # 2. SUIVI PAR CLASSE
    elif choix == "📊 Suivi par Classe":
        st.title("📈 Registre des Présences")
        if st.session_state.db_presences:
            df = pd.DataFrame(st.session_state.db_presences)
            
            classe_filt = st.selectbox("Filtrer par Classe :", ["Toutes"] + df['Classe'].unique().tolist())
            
            if classe_filt != "Toutes":
                df_view = df[df['Classe'] == classe_filt]
            else:
                df_view = df
                
            st.write(f"Nombre d'étudiants présents : {len(df_view)}")
            st.dataframe(df_view, use_container_width=True)
        else:
            st.info("Aucune donnée de présence enregistrée.")

    # 3. CALCULATEUR DE RÉSULTATS DYNAMIQUE
    elif choix == "🎓 Calculateur de Résultats":
        st.title("🧮 Calculateur de Bulletin")
        nb = st.number_input("Nombre de cours :", 1, 15, 3)
        
        notes = []
        max_p = []
        st.write("Saisissez les notes :")
        c = st.columns(3)
        for i in range(int(nb)):
            with c[i%3]:
                n = st.number_input(f"Note {i+1}", 0, 100, 10, key=f"n{i}")
                m = st.number_input(f"Max {i+1}", 10, 100, 20, key=f"m{i}")
                notes.append(n)
                max_p.append(m)
        
        if st.button("CALCULER"):
            pourcent = (sum(notes)/sum(max_p)) * 100
            st.metric("POURCENTAGE FINAL", f"{round(pourcent, 2)}%")
            if pourcent >= 80: st.success("MENTION : ÉLITE 🌟")
            elif pourcent >= 70: st.success("MENTION : DISTINCTION 🎓")
            elif pourcent >= 50: st.warning("MENTION : SATISFACTION ✅")
            else: st.error("MENTION : ÉCHEC ❌")
