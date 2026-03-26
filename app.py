import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
from io import BytesIO
import os

# --- 1. CONFIGURATION DU DESIGN ---
st.set_page_config(page_title="EduTracer UPL Pro", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    .main { background-color: #f0f4f8; }
    .stButton>button { width: 100%; border-radius: 15px; background: linear-gradient(135deg, #004e92, #000428); color: white; font-weight: bold; border: none; height: 3.5em; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0px 5px 15px rgba(0,0,0,0.2); }
    .card-pro { background-color: white; padding: 30px; border-radius: 20px; box-shadow: 0px 10px 25px rgba(0,0,0,0.1); border-left: 8px solid #004e92; }
    
    /* Style de la Carte d'Étudiant Finale */
    .id-card-final { border: 2px solid #000; border-radius: 12px; padding: 20px; background: #fff; width: 420px; margin: auto; font-family: 'Arial', sans-serif; box-shadow: 0px 10px 20px rgba(0,0,0,0.2); }
    .card-header { background: #004e92; color: white; padding: 10px; text-align: center; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px; font-weight: bold; }
    .card-body { display: flex; gap: 15px; align-items: center; }
    .info-label { color: #555; font-size: 12px; margin: 0; }
    .info-value { color: #000; font-size: 14px; font-weight: bold; margin: 0 0 8px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTION DE LA BASE DE DONNÉES (PERSISTANTE) ---
FICHIER_PRESENCES = "registre_upl.csv"

# Fonction pour charger les présences depuis le fichier CSV
def charger_presences():
    if os.path.exists(FICHIER_PRESENCES):
        return pd.read_csv(FICHIER_PRESENCES)
    else:
        # Si le fichier n'existe pas, on crée une structure vide
        return pd.DataFrame(columns=['Matricule', 'Nom_Complet', 'Classe', 'Date', 'Heure', 'Mode'])

# Fonction pour ajouter une présence et sauvegarder
def enregistrer_presence(matricule, nom_complet, classe):
    df = charger_presences()
    now = datetime.now()
    # Création de la nouvelle ligne
    nouvelle_presence = {
        'Matricule': matricule,
        'Nom_Complet': nom_complet,
        'Classe': classe,
        'Date': now.strftime("%d/%m/%Y"),
        'Heure': now.strftime("%H:%M:%S"),
        'Mode': 'QR Code'
    }
    # Ajout et sauvegarde
    df = pd.concat([df, pd.DataFrame([nouvelle_presence])], ignore_index=True)
    df.to_csv(FICHIER_PRESENCES, index=False)
    return nouvelle_presence

# --- 3. SÉCURITÉ ADMIN ---
# L'accès admin n'est visible que si l'URL contient ?admin=julien
params = st.query_params
is_admin = params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE 1 : SCANNER QR (PUBLIC / ÉLÈVE)
# ---------------------------------------------------------
if not is_admin:
    st.markdown("<h1 style='text-align: center; color: #004e92;'>🛡️ EduTracer : Portail de Pointage UPL</h1>", unsafe_allow_html=True)
    st.write(f"<p style='text-align: center;'>{datetime.now().strftime('%d %B %Y | %H:%M')}</p>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.markdown("<div class='card-pro'>", unsafe_allow_html=True)
        st.subheader("📷 Scanner la Carte")
        st.camera_input("Présentez le QR Code devant l'objectif")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_right:
        st.subheader("📝 Validation")
        # Champ pour simuler le contenu du QR Code pour ta démo
        qr_content = st.text_input("Simuler Scan QR (Format: Matricule|Nom|Classe)", placeholder="Saisir pour tester...")
        
        if st.button("CONFIRMER LA PRÉSENCE", use_container_width=True):
            if qr_content:
                # On sépare les infos (format attendu: Matricule|Nom_Complet|Classe)
                try:
                    infos = qr_content.split("|")
                    mat_q = infos[0]
                    nom_q = infos[1]
                    cl_q = infos[2]
                    
                    # 1. Enregistrement persistant dans le CSV
                    data_saved = enregistrer_presence(mat_q, nom_q, cl_q)
                    
                    # 2. Affichage de confirmation
                    st.markdown(f"""
                    <div class='card-pro' style='border-left-color: #28a745;'>
                        <h3 style='color: #28a745;'>✅ ÉTUDIANT IDENTIFIÉ</h3>
                        <p><b>Nom Complet :</b> {nom_q}</p>
                        <p><b>Classe :</b> {cl_q}</p>
                        <p><b>Matricule :</b> {mat_q}</p>
                        <p style='color: gray; font-size: 12px;'>Pointage réussi à {data_saved['Heure']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                    
                except:
                    st.error("❌ Format de QR Code invalide. Attendu: Matricule|Nom|Classe")
            else:
                st.warning("Veuillez scanner ou saisir le contenu du QR Code.")

# ---------------------------------------------------------
# INTERFACE 2 : PANEL ADMINISTRATION (CACHÉE)
# ---------------------------------------------------------
else:
    st.sidebar.title("👨‍💻 Admin : Julien")
    choix = st.sidebar.radio("Outils :", ["📊 Suivi par Classe", "🪪 Générateur de Cartes", "🎓 Calculateur"])

    # --- SOUS-PAGE : SUIVI PAR CLASSE (FIXÉ) ---
    if choix == "📊 Suivi par Classe":
        st.title("📈 Journal des Présences Officiel (UPL)")
        df_p = charger_presences() # On charge depuis le CSV local
        
        if not df_p.empty:
            st.write(f"Total des présences enregistrées : **{len(df_p)}**")
            # Filtre par classe
            classe_view = st.selectbox("Filtrer par classe :", ["Toutes"] + df_p['Classe'].unique().tolist())
            
            if classe_view != "Toutes":
                df_view = df_p[df_p['Classe'] == classe_view]
            else:
                df_view = df_p
            
            st.dataframe(df_view, use_container_width=True)
            
            # Bouton de téléchargement pour le secrétariat
            csv_data = df_p.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger le rapport CSV", csv_data, "registre_upl.csv", "text/csv")
        else:
            st.info("Aucune présence n'a encore été enregistrée dans la base de données.")

    # --- SOUS-PAGE : GÉNÉRATEUR DE CARTES (FIXÉ AVEC IDENTITÉS) ---
    elif choix == "🪪 Générateur de Cartes":
        st.title("🛠️ Création de Carte d'Étudiant Sécurisée")
        st.write("Remplissez TOUS les champs ci-dessous pour générer la carte officielle.")
        
        with st.form("form_carte"):
            c1, c2 = st.columns(2)
            mat = c1.text_input("Matricule (ID)")
            nom = c2.text_input("Nom")
            postnom = c1.text_input("Postnom")
            prenom = c2.text_input("Prénom")
            classe = st.selectbox("Classe", ["Bac 1 IA", "Bac 2 IA", "L1 INFO", "L2 INFO"])
            
            submit = st.form_submit_button("GÉNÉRER LA CARTE OFFICIELLE")
            
            if submit and mat and nom and classe:
                # 1. Préparation du QR Code (format: Matricule|Nom Postnom Prenom|Classe)
                nom_complet = f"{nom.upper()} {postnom.upper()} {prenom.title()}"
                data_qr = f"{mat}|{nom_complet}|{classe}"
                
                qr = qrcode.make(data_qr)
                buf = BytesIO()
                qr.save(buf, format="PNG")
                
                st.divider()
                st.subheader("Rendu de la Carte d'Étudiant à Imprimer")
                
                # 2. Design de la Carte Finale (AVEC IDENTITÉS COMPLÈTES)
                st.markdown(f"""
                <div class="id-card-final">
                    <div class="card-header">UNIVERSITÉ PROTESTANTE DE LUBUMBASHI</div>
                    <div class="card-body">
                        <div style="flex: 1;">
                            <p class="info-label">NOM</p>
                            <p class="info-value">{nom.upper()}</p>
                            <p class="info-label">POSTNOM</p>
                            <p class="info-value">{postnom.upper()}</p>
                            <p class="info-label">PRÉNOM</p>
                            <p class="info-value">{prenom.title()}</p>
                            <p class="info-label">CLASSE</p>
                            <p class="info-value">{classe}</p>
                            <p class="info-label" style="color:#004e92;">MATRICULE ID</p>
                            <p class="info-value" style="color:#004e92; font-size: 16px;">{mat}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Affichage du QR Code associé
                st.image(buf, width=150, caption=f"Scan pour pointage de {mat}")
                st.success("Carte générée avec succès ! Prête pour impression.")
            elif submit:
                st.warning("Veuillez remplir au minimum Matricule, Nom et Classe.")

    # --- SOUS-PAGE : CALCULATEUR ---
    elif choix == "🎓 Calculateur":
        st.title("🧮 Calculateur de Résultats")
        st.write("Outil pour calculer les pourcentages globaux et mentions.")
        # ... (Garder le code du calculateur précédent) ...
        nb = st.number_input("Nombre de cours :", 1, 10, 3)
        cols = st.columns(3)
        notes = []
        max_p = []
        for i in range(int(nb)):
            with cols[i%3]:
                n = st.number_input(f"Note {i+1}", 0, 100, 10, key=f"n{i}")
                m = st.number_input(f"Max {i+1}", 10, 100, 20, key=f"m{i}")
                notes.append(n)
                max_p.append(m)
        if st.button("CALCULER"):
            pourcent = (sum(notes)/sum(max_p)) * 100
            st.metric("POURCENTAGE", f"{round(pourcent, 2)}%")
            if pourcent >= 70: st.success("DISTINCTION 🎓")
            elif pourcent >= 50: st.warning("SATISFACTION ✅")
            else: st.error("ÉCHEC ❌")
