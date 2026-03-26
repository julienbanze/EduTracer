import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="UPL EduTracer Pro", layout="wide")

# --- GESTION DE LA BASE DE DONNÉES (CSV) ---
DB_PATH = "registre_biometrique.csv"

def charger_donnees():
    if os.path.exists(DB_PATH):
        return pd.read_csv(DB_PATH)
    return pd.DataFrame(columns=["Matricule", "Nom", "Classe", "Date", "Heure"])

def sauvegarder_presence(eleve_dict):
    df = charger_donnees()
    now = datetime.now()
    nouvelle_ligne = {
        "Matricule": eleve_dict["Matricule"],
        "Nom": f"{eleve_dict['Nom']} {eleve_dict['Prenom']}",
        "Classe": eleve_dict["Classe"],
        "Date": now.strftime("%d/%m/%Y"),
        "Heure": now.strftime("%H:%M:%S")
    }
    df = pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
    df.to_csv(DB_PATH, index=False)
    return nouvelle_ligne

# --- ACCÈS ADMIN ---
is_admin = st.query_params.get("admin") == "julien"

# ---------------------------------------------------------
# INTERFACE CLIENT (SCANNER & BULLETIN)
# ---------------------------------------------------------
if not is_admin:
    menu = st.sidebar.radio("Navigation", ["📸 Présence Faciale", "📊 Calcul Bulletin"])

    if menu == "📸 Présence Faciale":
        st.title("🛡️ Pointage Biométrique UPL")
        
        col_cam, col_res = st.columns(2)
        
        with col_cam:
            st.subheader("Scanner le visage")
            st.camera_input("Reconnaissance en cours...", key="face_cam")
            # Simulation : dans ton projet, l'IA reconnaît le matricule
            input_id = st.text_input("ID Détecté par l'IA (Matricule) :")
            valider = st.button("VALIDER L'IDENTITÉ")

        with col_res:
            if valider and input_id:
                # Simulation d'une base d'élèves
                db_eleves = {"2025023061": {"Nom": "BANZE", "Prenom": "Julien", "Classe": "Bac 1 IA"},
                             "2025000123": {"Nom": "KABAMBA", "Prenom": "Marc", "Classe": "Bac 1 IA"}}
                
                if input_id in db_eleves:
                    eleve = db_eleves[input_id]
                    eleve["Matricule"] = input_id
                    
                    # ENREGISTREMENT RÉEL DANS LE CSV
                    info_saved = sauvegarder_presence(eleve)
                    
                    # AFFICHAGE IMMÉDIAT
                    st.success("✅ IDENTITÉ CONFIRMÉE")
                    st.markdown(f"""
                        **Étudiant :** {info_saved['Nom']}  
                        **Classe :** {info_saved['Classe']}  
                        **Statut :** Présence enregistrée à {info_saved['Heure']}
                    """)
                    st.balloons()
                else:
                    st.error("Étudiant non reconnu.")

    elif menu == "📊 Calcul Bulletin":
        st.title("🧮 Calculateur de Résultats")
        nb_cours = st.number_input("Nombre de cours :", 1, 15, 5)
        with st.form("bulletin"):
            notes = []
            max_p = []
            c = st.columns(3)
            for i in range(int(nb_cours)):
                with c[i%3]:
                    notes.append(st.number_input(f"Note {i+1}", 0.0, 100.0, 10.0))
                    max_p.append(st.number_input(f"Max {i+1}", 1.0, 100.0, 20.0))
            if st.form_submit_button("Calculer"):
                pourcentage = (sum(notes)/sum(max_p)) * 100
                st.metric("Résultat", f"{round(pourcentage, 2)}%")
                if pourcentage >= 70: st.success("DISTINCTION 🎓")
                elif pourcentage >= 50: st.info("SATISFACTION ✅")
                else: st.error("ÉCHEC ❌")

# ---------------------------------------------------------
# INTERFACE ADMIN (AFFICHAGE DES DONNÉES)
# ---------------------------------------------------------
else:
    st.title("👨‍💻 Administration : Julien")
    st.subheader("📈 Journal Biométrique en Temps Réel")
    
    # CHARGEMENT DES DONNÉES DEPUIS LE FICHIER CSV
    df_final = charger_donnees()
    
    if not df_final.empty:
        st.write(f"Nombre total de présences : **{len(df_final)}**")
        st.dataframe(df_final, use_container_width=True)
        # Option pour effacer la base (utile pour tes tests)
        if st.button("Effacer le registre"):
            os.remove(DB_PATH)
            st.rerun()
    else:
        st.warning("Aucun pointage enregistré dans la base de données CSV.")
