"""Interface Streamlit d'Anonymia : affichage et saisie uniquement, toute la logique est dans l'API."""

import time

import streamlit as st

import api_client as api

st.set_page_config(page_title="Anonymia", layout="wide")

# Écrans accessibles par rôle : un rôle hérite des écrans du rôle inférieur, comme dans le dossier.
ECRANS = {
    "UTILISATEUR": ["Caviarder un document"],
    "SUPERVISEUR": ["Caviarder un document", "Historique"],
    "ADMINISTRATEUR": ["Caviarder un document", "Historique", "Gestion des comptes"],
}


def entete():
    # HTML autorisé ici car le contenu est écrit par nous, jamais fourni par l'utilisateur.
    st.markdown("<h1 style='text-align:center; color:#185ABD;'>Anonymia</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; opacity:0.75;'>Caviardage de données personnelles"
        " dans les documents administratifs</p>",
        unsafe_allow_html=True,
    )


def page_connexion():
    entete()
    # Seule la colonne du milieu est utilisée : le formulaire reste centré et étroit.
    _, centre, _ = st.columns([1, 1.2, 1])
    with centre:
        if not api.api_disponible():
            st.error("L'API ne répond pas. Vérifiez qu'elle est lancée sur le port 5000.")
            return

        with st.form("connexion"):
            st.subheader("Connexion")
            email = st.text_input("Adresse e-mail")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            valider = st.form_submit_button("Se connecter", type="primary", use_container_width=True)

        if valider:
            try:
                reponse = api.connexion(email, mot_de_passe)
            except api.ApiError:
                # Message volontairement vague : on n'indique pas si c'est l'e-mail ou le mot de passe.
                st.error("E-mail ou mot de passe incorrect.")
                return
            # Conservé d'une page à l'autre ; le jeton accompagne chaque appel à l'API.
            st.session_state.utilisateur = {
                "id": reponse["id_person"],
                "email": reponse["email"],
                "token": reponse["access_token"],
                "role": api.role(reponse["id_person"], reponse["access_token"]),
            }
            st.rerun()


def barre_laterale() -> str:
    utilisateur = st.session_state.utilisateur
    with st.sidebar:
        st.markdown("### Anonymia")
        st.text(utilisateur["email"])
        st.caption(utilisateur["role"].capitalize())
        st.divider()
        # Un rôle inconnu n'obtient que les droits d'un simple utilisateur.
        ecran = st.radio("Menu", ECRANS.get(utilisateur["role"], ECRANS["UTILISATEUR"]))
        st.divider()
        if st.button("Se déconnecter", use_container_width=True):
            # On efface tout, y compris le dernier document, pour la personne suivante.
            st.session_state.clear()
            st.rerun()
    return ecran


def page_caviarder():
    st.subheader("Caviarder un document")

    onglet_fichier, onglet_texte = st.tabs(["Envoyer un fichier", "Coller un texte"])
    with onglet_fichier:
        fichier = st.file_uploader("Document au format texte (.txt ou .md)", type=["txt", "md"])
    with onglet_texte:
        texte_colle = st.text_area("Texte à caviarder", height=220)

    with st.expander("Options"):
        st.radio("Stratégie", ["Masquage"], help="La pseudonymisation sera disponible prochainement.")
        utiliser_llm = st.toggle("Utiliser le LLM (noms, adresses, lieux...)", value=True)

    if st.button("Caviarder", type="primary"):
        # Le fichier est prioritaire ; à défaut, le texte collé est envoyé comme un fichier.
        if fichier is not None:
            nom, contenu = fichier.name, fichier.getvalue()
        elif texte_colle.strip():
            nom, contenu = "texte_colle.txt", texte_colle.encode("utf-8")
        else:
            st.warning("Ajoutez un fichier ou collez un texte avant de lancer le caviardage.")
            return

        debut = time.perf_counter()
        try:
            with st.spinner("Analyse en cours, cela peut prendre quelques secondes..."):
                reponse = api.caviarder(st.session_state.utilisateur["token"], nom, contenu, utiliser_llm)
        except api.ApiError as erreur:
            st.error(f"Le caviardage a échoué ({erreur.status}) : {erreur.message}")
            return

        # L'original ne quitte pas l'interface ; il servira au surlignage des PII.
        st.session_state.resultat = {
            "original": contenu.decode("utf-8"),
            "reponse": reponse,
            "duree": time.perf_counter() - debut,
            "llm": utiliser_llm,
        }

    if "resultat" in st.session_state:
        st.text_area("Document caviardé", st.session_state.resultat["reponse"]["content"], height=300)


# Aiguillage principal : Streamlit réexécute ce fichier en entier à chaque interaction.
if "utilisateur" not in st.session_state:
    page_connexion()
else:
    ecran = barre_laterale()
    entete()
    if ecran == "Caviarder un document":
        page_caviarder()
    else:
        st.info("Cet écran sera construit dans une prochaine étape.")