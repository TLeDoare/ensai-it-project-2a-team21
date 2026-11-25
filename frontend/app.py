"""Interface Streamlit d'Anonymia : affichage et saisie uniquement, toute la logique est dans l'API."""
import html
import time

import api_client as api
import pandas as pd
import streamlit as st

from theme import apply_theme, couleur_pii, page_header, hero_header, legende_cercles, render_redacted, sidebar_brand

st.set_page_config(page_title="Anonymia", layout="wide")
apply_theme()

# Écrans accessibles par rôle : un rôle hérite des écrans du rôle inférieur, comme dans le dossier.
# « Mon compte » est accessible à tous : chacun peut changer son propre mot de passe.
ECRANS = {
    "UTILISATEUR": ["Caviarder un document", "Mon compte"],
    "SUPERVISEUR": ["Caviarder un document", "Historique", "Mon compte"],
    "ADMINISTRATEUR": ["Caviarder un document", "Historique", "Gestion des comptes", "Mon compte"],
}


def entete(titre: str, description: str = ""):
    # Bandeau teal en tête de chaque écran ; le sur-titre rappelle l'espace (rôle) de l'utilisateur.
    role = st.session_state.utilisateur["role"].lower()
    page_header(titre, description, eyebrow=f"Espace {role}")


def page_connexion():
    hero_header()
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
            except api.ApiError as erreur:
                # 403 : bons identifiants mais compte désactivé par un administrateur (F1)
                if erreur.status == 403:
                    st.error(erreur.message)
                else:
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
        sidebar_brand()
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
    """Renvoie le texte en HTML, chaque PII détectée surlignée selon son cercle."""
    texte = texte.replace("\r", "")
    morceaux = []
    position = 0
    for d in sorted(details, key=lambda d: d["start"]):
        if d["start"] < position:
            continue
        couleur = couleur_pii(d["type"])
        morceaux.append(html.escape(texte[position:d["start"]]))
        morceaux.append(
            f"<mark style='background:{couleur};' title='{html.escape(d['type'])}'>"
            f"{html.escape(texte[d['start']:d['end']])}</mark>"
        )
        position = d["end"]
    morceaux.append(html.escape(texte[position:]))
    return '<div class="anm-texte">' + "".join(morceaux) + "</div>"


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
        legende_cercles()
        with st.container(border=True, height=420):
            st.markdown(surligner(resultat["original"], details), unsafe_allow_html=True)
    with droite:
        st.markdown("**Texte caviardé**")
        st.markdown('<div class="anm-legende">&nbsp;</div>', unsafe_allow_html=True)
        with st.container(border=True, height=420):
            st.markdown(render_redacted(reponse["content"]), unsafe_allow_html=True)

    # --- Comparaison côte à côte des détecteurs (FO4), repliée par défaut pour alléger l'affichage ---
    with st.expander("Comparer les détecteurs (regex / LLM)"):
        # Sépare les PII selon le détecteur qui les a trouvées (champ "source" renvoyé par l'API)
        pii_regex = [d for d in details if d["source"] == "Regex"]
        pii_llm = [d for d in details if d["source"] == "LLM"]
        col_regex, col_llm = st.columns(2)
        with col_regex:
            st.markdown(f"Expressions régulières ({len(pii_regex)} PII)")
            with st.container(border=True, height=300):
                # Texte d'origine surligné uniquement avec les PII trouvées par les regex
                st.markdown(surligner(resultat["original"], pii_regex), unsafe_allow_html=True)
        with col_llm:
            st.markdown(f"LLM ({len(pii_llm)} PII)")
            with st.container(border=True, height=300):
                # Texte d'origine surligné uniquement avec les PII trouvées par le LLM
                st.markdown(surligner(resultat["original"], pii_llm), unsafe_allow_html=True)
        # Types propres à chaque détecteur : montre leur complémentarité
        types_regex = {d["type"] for d in pii_regex}
        types_llm = {d["type"] for d in pii_llm}
        st.caption(
            "Types trouvés seulement par les regex : " + (", ".join(sorted(types_regex - types_llm)) or "aucun")
            + " | seulement par le LLM : " + (", ".join(sorted(types_llm - types_regex)) or "aucun")
        )
        # Nombre de PII par type pour chaque détecteur, côte à côte
        if details:
            st.dataframe(
                pd.crosstab(pd.Series([d["type"] for d in details], name="Type"),
                            pd.Series([d["source"] for d in details], name="Détecteur")),
                use_container_width=True,
            )
        st.caption(
            "Une donnée trouvée par les deux détecteurs n'est comptée qu'une fois, "
            "sous le détecteur retenu lors de la fusion des chevauchements."
        )

    # FO2 : comparaison du pipeline classique et de la réécriture directe par le LLM
    if "direct" in resultat or "direct_erreur" in resultat:
        with st.expander("Comparer avec l'anonymisation directe par le LLM", expanded=True):
            if "direct_erreur" in resultat:
                st.error("La réécriture directe a échoué : " + resultat["direct_erreur"])
            else:
                col_classique, col_direct = st.columns(2)
                with col_classique:
                    st.markdown("**Pipeline classique** (détection puis remplacement)")
                    with st.container(border=True, height=300):
                        st.markdown(render_redacted(reponse["content"]), unsafe_allow_html=True)
                with col_direct:
                    st.markdown("**Réécriture directe par le LLM**")
                    with st.container(border=True, height=300):
                        st.markdown(surligner(resultat["direct"], []), unsafe_allow_html=True)
                st.caption(
                    "La réécriture directe n'est pas vérifiable : on ne sait pas quelles données le LLM a remplacées, "
                    "ni s'il en a oublié. Elle sert à comparer, pas à diffuser ; elle n'est pas enregistrée dans l'historique."
                )

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
    entete("Caviarder un document",
                "Envoyez un fichier .txt / .md ou collez un texte : les données personnelles sont repérées puis masquées.")

    onglet_fichier, onglet_texte = st.tabs(["Envoyer un fichier", "Coller un texte"])
    with onglet_fichier:
        fichier = st.file_uploader("Document au format texte (.txt ou .md)", type=["txt", "md"])
    with onglet_texte:
        texte_colle = st.text_area("Texte à caviarder", height=220)

    with st.expander("Options"):
        strategie = st.radio("Stratégie", ["Masquage", "Pseudonymisation"], index=0)
        utiliser_llm = st.toggle("Utiliser le LLM (noms, adresses, lieux...)", value=True)
        # FO2 : second appel, indépendant du premier, où le LLM réécrit lui-même le document
        comparer_direct = st.toggle("Comparer avec l'anonymisation directe par le LLM", value=False)

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

        # FO2 : un échec de ce second appel n'empêche pas d'afficher le caviardage classique
        if comparer_direct:
            try:
                with st.spinner("Réécriture directe par le LLM..."):
                    # Même stratégie que le caviardage classique, pour comparer ce qui est comparable
                    direct = api.anonymiser_par_llm(
                        st.session_state.utilisateur["token"], nom, contenu, masquer=(strategie == "Masquage")
                    )
                st.session_state.resultat["direct"] = direct["content"]
            except api.ApiError as erreur:
                st.session_state.resultat["direct_erreur"] = f"{erreur.message} ({erreur.status})"

    if "resultat" in st.session_state:
        afficher_resultat(st.session_state.resultat)

def page_historique():
    entete("Historique des traitements", "Documents déjà caviardés, avec les types de données détectés.")

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
                # Paramètres du traitement, enregistrés dans le journal (F4)
                "Stratégie": "Masquage" if d["params"].get("mask", True) else "Pseudonymisation",
                "LLM": "Oui" if d["params"].get("llm", True) else "Non",
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

    # Toutes les PII des documents encore visibles après les filtres (pour les graphiques ci-dessous)
    numeros_visibles = set(tableau["N°"])
    pii_visibles = pd.DataFrame(
        [pii for doc in documents if doc["id"] in numeros_visibles for pii in doc["details"]],
        columns=["start", "end", "type", "confidence", "source"],
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Documents traités", len(tableau))
    col2.metric("PII détectées au total", int(tableau["PII détectées"].sum()))
    # Moyenne arrondie à une décimale ; 0 si aucun document ne correspond aux filtres
    col3.metric("PII par document (moyenne)", round(tableau["PII détectées"].mean(), 1) if len(tableau) else 0)

    # --- Graphiques des indicateurs d'activité (F4), regroupés en trois onglets ---
    onglet_activite, onglet_donnees, onglet_usage = st.tabs(["Activité", "Données détectées", "Usage"])
    with onglet_activite:
        graphique_jours, graphique_auteurs = st.columns(2)
        with graphique_jours:
            st.markdown("**Documents traités par jour**")
            # Compte les documents filtrés pour chaque date
            st.bar_chart(tableau.groupby(tableau["Date"].dt.date).size())
        with graphique_auteurs:
            st.markdown("**Documents traités par auteur**")
            st.bar_chart(tableau["Auteur"].value_counts())
    with onglet_donnees:
        if pii_visibles.empty:
            st.info("Aucune PII sur la période choisie.")
        else:
            graphique_types, graphique_sources = st.columns(2)
            with graphique_types:
                st.markdown("**Fréquence des types de PII**")
                st.bar_chart(pii_visibles["type"].value_counts())
            with graphique_sources:
                st.markdown("**PII par détecteur (regex ou LLM)**")
                st.bar_chart(pii_visibles["source"].value_counts())
            # Croisement type x détecteur : quel détecteur trouve quel type de donnée
            st.markdown("**Types de PII selon le détecteur**")
            st.dataframe(pd.crosstab(pii_visibles["type"], pii_visibles["source"]), use_container_width=True)
    with onglet_usage:
        graphique_strategie, graphique_llm = st.columns(2)
        with graphique_strategie:
            st.markdown("**Stratégie de caviardage choisie**")
            st.bar_chart(tableau["Stratégie"].value_counts())
        with graphique_llm:
            st.markdown("**Traitements avec ou sans LLM**")
            st.bar_chart(tableau["LLM"].value_counts())

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
        # Lire le texte du document sans planter s'il est absent
        contenu = document.get("content") if document else None
        if contenu is None:
            # Document sans texte disponible : message au lieu d'une erreur
            st.info("Par conception, le contenu des documents n'est pas conservé : seuls l'empreinte et les types de PII détectés sont journalisés.")
        else:
            # Cas normal : afficher le texte caviardé
            st.markdown(render_redacted(contenu), unsafe_allow_html=True)
    types = sorted({d["type"] for d in document["details"]})
    st.caption("Types détectés : " + (", ".join(types) if types else "aucun"))

def page_comptes():
    entete("Gestion des comptes")
    token = st.session_state.utilisateur["token"]

    # --- Liste des comptes existants ---
    try:
        comptes = api.utilisateurs(token)
    except api.ApiError as erreur:
        st.error(f"Impossible de charger les comptes ({erreur.status}) : {erreur.message}")
        return

    if comptes:
        # Le mot de passe haché n'est jamais affiché : seules l'identité et le rôle sont utiles ici.
        tableau = pd.DataFrame(
            [
                {
                    "N°": c.get("id"),
                    "E-mail": c.get("email"),
                    "Rôle": c.get("role"),
                    # Statut F1 : un compte désactivé est conservé mais ne peut plus se connecter
                    "Statut": "Actif" if c.get("active", True) else "Désactivé",
                }
                for c in comptes
            ]
        )
                # Un compteur pour le total, puis un par rôle (0 si aucun compte n'a ce rôle)
        colonnes = st.columns(4)
        colonnes[0].metric("Comptes", len(tableau))
        for colonne, (role_nom, libelle) in zip(
            colonnes[1:],
            [("UTILISATEUR", "Utilisateurs"), ("SUPERVISEUR", "Superviseurs"), ("ADMINISTRATEUR", "Administrateurs")],
        ):
            colonne.metric(libelle, int((tableau["Rôle"] == role_nom).sum()))
        st.dataframe(tableau.sort_values("N°"), hide_index=True, width="stretch")
    else:
        st.info("Aucun compte trouvé.")

    st.divider()

               # --- Trois boutons d'action : un clic ouvre le panneau, un second clic le referme ---
    if "action_compte" not in st.session_state:
        st.session_state.action_compte = None

    def basculer(action: str):
        """Ouvre le panneau demandé, ou le referme s'il est déjà ouvert."""
        st.session_state.action_compte = None if st.session_state.action_compte == action else action

    col_creer, col_modifier, col_statut, col_supprimer = st.columns(4)
    col_creer.button("Créer un compte", type="primary", use_container_width=True,
                     on_click=basculer, args=("creer",))
    col_modifier.button("Modifier un compte", type="primary", use_container_width=True,
                        on_click=basculer, args=("modifier",), disabled=not comptes)
    col_statut.button("Activer / désactiver", type="primary", use_container_width=True,
                      on_click=basculer, args=("statut",), disabled=not comptes)
    col_supprimer.button("Supprimer un compte", type="primary", use_container_width=True,
                         on_click=basculer, args=("supprimer",), disabled=not comptes)

    action = st.session_state.action_compte
    # Liste des comptes au format lisible, partagée par les panneaux Modifier, Statut et Supprimer
    choix = {f"{c['email']} ({c['role']})": c for c in comptes} if comptes else {}
    roles = list(ECRANS.keys())

    # --- Panneau Créer ---
    if action == "creer":
        with st.form("creation_compte", clear_on_submit=True):
            st.markdown("**Créer un compte**")
            email = st.text_input("Adresse e-mail")
            mot_de_passe = st.text_input(
                "Mot de passe provisoire",
                type="password",
                help="8 caractères minimum, avec une minuscule, une majuscule, un chiffre et un caractère spécial.",
            )
            role_compte = st.selectbox("Rôle", roles)
            valider = st.form_submit_button("Valider la création", type="primary")
        if valider:
            if not email.strip() or not mot_de_passe:
                st.warning("L'e-mail et le mot de passe sont obligatoires.")
                return
            # Mêmes exigences que l'API : chaque règle non respectée est listée pour l'utilisateur
            regles = [
                (len(mot_de_passe) >= 8, "8 caractères minimum"),
                (any(c.islower() for c in mot_de_passe), "une minuscule"),
                (any(c.isupper() for c in mot_de_passe), "une majuscule"),
                (any(c.isdigit() for c in mot_de_passe), "un chiffre"),
                (any(c in "!@#%^&(),.?\":{}|<>_-+=" for c in mot_de_passe), "un caractère spécial"),
            ]
            manquantes = [libelle for respectee, libelle in regles if not respectee]
            if manquantes:
                st.warning("Mot de passe trop faible. Il manque : " + ", ".join(manquantes) + ".")
                return
            try:
                api.creer_compte(token, email.strip(), mot_de_passe, role_compte)
            except api.ApiError as erreur:
                st.error(f"La création a échoué ({erreur.status}) : {erreur.message}")
                return
            st.success(f"Compte {email.strip()} créé avec le rôle {role_compte}.")
            st.rerun()

    # --- Panneau Modifier ---
    elif action == "modifier":
        st.markdown("**Modifier le rôle d'un compte**")
        compte = choix[st.selectbox("Compte", list(choix.keys()), key="compte_modif")]
        nouveau_role = st.selectbox("Nouveau rôle", roles, index=roles.index(compte["role"]))
        if st.button("Enregistrer le rôle", type="primary"):
            try:
                api.changer_role(token, compte["id"], nouveau_role)
                st.success(f"{compte['email']} a maintenant le rôle {nouveau_role}.")
                st.rerun()
            except api.ApiError as erreur:
                st.error(f"Changement refusé ({erreur.status}) : {erreur.message}")

    # --- Panneau Activer / désactiver ---
    elif action == "statut":
        st.markdown("**Activer ou désactiver un compte**")
        st.caption("Un compte désactivé est conservé avec son historique, mais ne peut plus se connecter.")

        # Message de réussite conservé après le rechargement de la page (st.rerun efface l'affichage)
        if "message_statut" in st.session_state:
            st.success(st.session_state.pop("message_statut"))

        compte = choix[st.selectbox("Compte", list(choix.keys()), key="compte_statut")]
        actif = compte.get("active", True)
        st.write(f"Statut actuel : **{'Actif' if actif else 'Désactivé'}**")
        # Le bouton propose l'action inverse du statut actuel
        libelle = "Désactiver ce compte" if actif else "Réactiver ce compte"
        if st.button(libelle, type="primary"):
            try:
                api.changer_statut(token, compte["id"], not actif)
                etat = "désactivé" if actif else "réactivé"
                st.session_state["message_statut"] = f"Compte {compte['email']} {etat}."
                st.rerun()
            except api.ApiError as erreur:
                st.error(f"Changement refusé ({erreur.status}) : {erreur.message}")

    # --- Panneau Supprimer ---
    elif action == "supprimer":
        st.markdown("**Supprimer un compte**")

        # Message de réussite conservé après le rechargement de la page (st.rerun efface l'affichage)
        if "message_suppression" in st.session_state:
            st.success(st.session_state.pop("message_suppression"))

        compte = choix[st.selectbox("Compte", list(choix.keys()), key="compte_suppr")]

        @st.dialog("Confirmer la suppression")
        def confirmer_suppression(compte_cible: dict):
            """Fenêtre modale : la suppression n'a lieu qu'après une validation explicite, compte par compte."""
            st.write(f"Voulez-vous vraiment supprimer le compte **{compte_cible['email']}** ?")
            st.caption("Cette action est définitive : le compte ne pourra pas être restauré.")
            col_annuler, col_supprimer = st.columns(2)
            # Annuler : ferme simplement la fenêtre, sans rien modifier
            if col_annuler.button("Annuler", use_container_width=True):
                st.rerun()
            # Supprimer : appel à l'API, puis fermeture de la fenêtre et rechargement de la liste
            if col_supprimer.button("Supprimer", type="primary", use_container_width=True):
                try:
                    api.supprimer_compte(token, compte_cible["id"])
                    st.session_state["message_suppression"] = f"Compte {compte_cible['email']} supprimé."
                    st.rerun()
                except api.ApiError as erreur:
                    st.error(f"Suppression refusée ({erreur.status}) : {erreur.message}")

        # Le bouton ouvre seulement la fenêtre : aucune suppression directe depuis la page
        if st.button("Supprimer ce compte", type="primary"):
            confirmer_suppression(compte)

def page_mon_compte():
    entete("Mon compte")
    utilisateur = st.session_state.utilisateur
    # E-mail et rôle affichés en lecture seule : seul un administrateur peut changer le rôle,
    # et l'e-mail n'est pas modifiable (identifiant de connexion et clé du journal d'audit)
    st.text_input("Adresse e-mail", value=utilisateur["email"], disabled=True)
    st.caption(f"Rôle : {utilisateur['role'].capitalize()}. Pour changer de rôle, contactez un administrateur.")

    with st.form("changer_mot_de_passe", clear_on_submit=True):
        st.markdown("**Changer mon mot de passe**")
        mot_de_passe = st.text_input(
            "Nouveau mot de passe",
            type="password",
            help="8 caractères minimum, avec une minuscule, une majuscule, un chiffre et un caractère spécial.",
        )
        confirmation = st.text_input("Confirmer le nouveau mot de passe", type="password")
        valider = st.form_submit_button("Enregistrer", type="primary")

    if not valider:
        return
    if not mot_de_passe:
        st.warning("Saisissez un nouveau mot de passe.")
        return
    if mot_de_passe != confirmation:
        st.warning("Les deux mots de passe ne sont pas identiques.")
        return
    # Mêmes règles que pour la création de compte, vérifiées avant l'envoi
    regles = [
        (len(mot_de_passe) >= 8, "8 caractères minimum"),
        (any(c.islower() for c in mot_de_passe), "une minuscule"),
        (any(c.isupper() for c in mot_de_passe), "une majuscule"),
        (any(c.isdigit() for c in mot_de_passe), "un chiffre"),
        (any(c in "!@#%^&(),.?\":{}|<>_-+=" for c in mot_de_passe), "un caractère spécial"),
    ]
    manquantes = [libelle for respectee, libelle in regles if not respectee]
    if manquantes:
        st.warning("Mot de passe trop faible. Il manque : " + ", ".join(manquantes) + ".")
        return

    try:
        # L'e-mail actuel est renvoyé tel quel : l'API exige le champ mais ne le modifie pas
        api.modifier_mon_compte(utilisateur["token"], utilisateur["id"], utilisateur["email"], mot_de_passe)
    except api.ApiError as erreur:
        st.error(f"La modification a échoué ({erreur.status}) : {erreur.message}")
        return
    st.success("Votre mot de passe a été modifié. Utilisez-le à votre prochaine connexion.")

# Aiguillage principal : Streamlit réexécute ce fichier en entier à chaque interaction.
if "utilisateur" not in st.session_state:
    page_connexion()
else:
    # Chaque écran affiche son propre en-tête (page_header) avec son titre.
    ecran = barre_laterale()
    if ecran == "Caviarder un document":
        page_caviarder()
    elif ecran == "Historique":
        page_historique()
    elif ecran == "Gestion des comptes":
        page_comptes()
    elif ecran == "Mon compte":
        page_mon_compte()
    else:
        entete(ecran)
        st.info("Cet écran sera construit dans une prochaine étape.")
