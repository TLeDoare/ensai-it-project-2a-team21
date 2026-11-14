"""Interface Streamlit d'Anonymia : affichage et saisie uniquement, toute la logique est dans l'API."""
import html
import time

import api_client as api
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Anonymia", layout="wide")

# Écrans accessibles par rôle : un rôle hérite des écrans du rôle inférieur, comme dans le dossier.
ECRANS = {
    "UTILISATEUR": ["Caviarder un document"],
    "SUPERVISEUR": ["Caviarder un document", "Historique"],
    "ADMINISTRATEUR": ["Caviarder un document", "Historique", "Gestion des comptes"],
}

# Couleur de surlignage par type de PII ; les types absents de la liste sont en gris.
COULEURS = {
    "name": "#FFD6A5",
    "address": "#CAFFBF",
    "email": "#9BF6FF",
    "phone_number": "#BDB2FF",
    "birthdate": "#FFADAD",
    "place": "#FDFFB6",
    "organism": "#FFC6FF",
    "NIR": "#A0C4FF",
    "IBAN": "#A0C4FF",
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
            try:
                api.deconnexion(utilisateur["token"])

            except api.ApiError as erreur:
                if erreur.status != 401:
                    st.error(
                        "La déconnexion n'a pas pu être confirmée "
                        "par le serveur. Veuillez réessayer."
                    )
                    return ecran

            # Le jeton a été révoqué ou était déjà invalide.
            # On efface toutes les données de la session Streamlit.
            st.session_state.clear()
            st.rerun()

    return ecran


def surligner(texte: str, details: list) -> str:
    """Renvoie le texte en HTML, avec chaque PII détectée surlignée selon son type."""
    morceaux = []
    position = 0
    for d in sorted(details, key=lambda d: d["start"]):
        if d["start"] < position:
            continue
        couleur = COULEURS.get(d["type"], "#E0E0E0")
        morceaux.append(html.escape(texte[position:d["start"]]))
        morceaux.append(
            f"<mark style='background:{couleur}; padding:0 3px; border-radius:4px;' title='{d['type']}'>"
            f"{html.escape(texte[d['start']:d['end']])}</mark>"
        )
        position = d["end"]
    morceaux.append(html.escape(texte[position:]))
    return "".join(morceaux).replace("\r", "").replace("\n", "<br>")


def afficher_resultat(resultat: dict):
    reponse = resultat["reponse"]
    details = reponse["details"]
    nb_regex = sum(1 for d in details if d["source"] == "Regex")
    nb_llm = sum(1 for d in details if d["source"] == "LLM")

    st.divider()
    st.subheader("Résultat")

    if resultat["llm"] and nb_llm == 0:
        st.warning(
            "Le LLM n'a rien détecté : il est peut-être indisponible (mode dégradé). "
            "Seules les détections par expressions régulières ont été appliquées."
        )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("PII détectées", len(details))
    col2.metric("Expressions régulières", nb_regex)
    col3.metric("LLM", nb_llm)
    col4.metric("Durée", f"{resultat['duree']:.1f} s")

    # Le texte est passé par html.escape avant affichage : il ne peut pas injecter de HTML.
    gauche, droite = st.columns(2)
    with gauche:
        st.markdown("**Texte d'origine**")
        with st.container(border=True, height=420):
            st.markdown(surligner(resultat["original"], details), unsafe_allow_html=True)
    with droite:
        st.markdown("**Texte caviardé**")
        with st.container(border=True, height=420):
            st.markdown(surligner(reponse["content"], []), unsafe_allow_html=True)

    st.download_button(
        "Télécharger le document caviardé",
        reponse["content"],
        file_name="document_caviarde.txt",
        type="primary",
    )

    with st.expander(f"Détail des {len(details)} PII détectées"):
        lignes = [
            {
                "Type": d["type"],
                "Texte": resultat["original"][d["start"]:d["end"]],
                "Détecteur": d["source"],
                "Confiance": d["confidence"],
            }
            for d in sorted(details, key=lambda d: d["start"])
        ]
        st.dataframe(lignes, hide_index=True, use_container_width=True)

    st.caption("Relecture humaine obligatoire avant toute diffusion : aucun détecteur n'est infaillible.")


def page_caviarder():
    st.subheader("Caviarder un document")

    onglet_fichier, onglet_texte = st.tabs(["Envoyer un fichier", "Coller un texte"])
    with onglet_fichier:
        fichier = st.file_uploader("Document au format texte (.txt ou .md)", type=["txt", "md"])
    with onglet_texte:
        texte_colle = st.text_area("Texte à caviarder", height=220)

    with st.expander("Options"):
        strategie = st.radio("Stratégie", ["Masquage", "Pseudonymisation"], index=0)
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
                reponse = api.caviarder(st.session_state.utilisateur["token"], nom, contenu, utiliser_llm, masquer=(strategie == "Masquage"))
        except api.ApiError as erreur:
            st.error(f"Le caviardage a échoué ({erreur.status}) : {erreur.message}")
            return

        # L'original ne quitte pas l'interface ; il sert uniquement au surlignage.
        st.session_state.resultat = {
            "original": contenu.decode("utf-8"),
            "reponse": reponse,
            "duree": time.perf_counter() - debut,
            "llm": utiliser_llm,
        }

    if "resultat" in st.session_state:
        afficher_resultat(st.session_state.resultat)

def page_historique():
    st.subheader("Historique des traitements")

    try:
        documents = api.historique(st.session_state.utilisateur["token"])
    except api.ApiError as erreur:
        st.error(f"Impossible de charger l'historique ({erreur.status}) : {erreur.message}")
        return
    if not documents:
        st.info("Aucun document n'a encore été traité.")
        return

    # Seules les métadonnées et le texte caviardé sont conservés par l'API (F4), jamais l'original.
    tableau = pd.DataFrame(
        [
            {
                "N°": d["id"],
                "Date": pd.to_datetime(d["upload_date"]),
                "Auteur": d["sent_by"],
                "PII détectées": len(d["details"]),
                "Empreinte": d["hash"][:12],
            }
            for d in documents
        ]
    )

    filtre_auteur, filtre_date = st.columns(2)
    auteurs = filtre_auteur.multiselect("Auteur", sorted(tableau["Auteur"].unique()))
    periode = filtre_date.date_input(
        "Période", value=(tableau["Date"].min().date(), tableau["Date"].max().date())
    )
    if auteurs:
        tableau = tableau[tableau["Auteur"].isin(auteurs)]
    # Pendant la sélection, date_input ne renvoie qu'une date : on attend d'avoir les deux bornes.
    if len(periode) == 2:
        tableau = tableau[tableau["Date"].dt.date.between(periode[0], periode[1])]

    col1, col2 = st.columns(2)
    col1.metric("Documents traités", len(tableau))
    col2.metric("PII détectées au total", int(tableau["PII détectées"].sum()))

    st.dataframe(
        tableau.sort_values("Date", ascending=False),
        hide_index=True,
        use_container_width=True,
        column_config={"Date": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm")},
    )

    if tableau.empty:
        return
    numero = st.selectbox("Voir le détail du document n°", tableau["N°"].tolist())
    document = next(d for d in documents if d["id"] == numero)
    with st.container(border=True):
        st.markdown(surligner(document["content"], []), unsafe_allow_html=True)
    types = sorted({d["type"] for d in document["details"]})
    st.caption("Types détectés : " + (", ".join(types) if types else "aucun"))

# Aiguillage principal : Streamlit réexécute ce fichier en entier à chaque interaction.
if "utilisateur" not in st.session_state:
    page_connexion()
else:
    ecran = barre_laterale()
    entete()
    if ecran == "Caviarder un document":
        page_caviarder()
    elif ecran == "Historique":
        page_historique()
    else:
        st.info("Cet écran sera construit dans une prochaine étape.")