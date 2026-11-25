"""Thème visuel Anonymia pour Streamlit.

Applique le système de design (couleurs, polices, composants) à l'interface.
Le HTML injecté ici est écrit par nous ; tout texte venant de l'utilisateur
ou de l'API est passé par html.escape avant affichage.
"""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

import streamlit as st

# --- Tokens (identiques au système de design) ---------------------------
TEAL_900 = "#072E2B"
TEAL_700 = "#0E3B38"
TEAL_500 = "#1C5F59"
TEAL_50 = "#E7F0EE"
GOLD_700 = "#9A7A2C"
GOLD_500 = "#C8A24A"
GOLD_100 = "#F4EAD0"
INK_900 = "#121216"
INK_500 = "#55555F"
SILVER_100 = "#E9ECEF"
ROSE_100 = "#F3DADA"
ROSE_700 = "#8A2B2B"

# --- Couleur de surlignage par cercle de la typologie --------------------
# Cercle 1 : identifiants directs ; cercle 2 : identification indirecte ;
# cercle 3 : catégories sensibles. Un type inconnu est en gris argent.
CERCLE_1 = {"name", "last_name", "first_name", "address", "email", "phone_number",
            "NIR", "IBAN", "PAN", "CNI", "EX_CNI"}
CERCLE_2 = {"place", "organism", "birthdate", "SIREN", "IP_V4", "IP_V6", "IP",
            "immatriculation", "cadastre", "GPS", "postal_code", "job"}
CERCLE_3 = {"medical", "ethnicity", "gender", "income", "judiciary_situation",
            "family_relationships", "private_life"}


def couleur_pii(pii_type: str) -> str:
    """Couleur de fond du surlignage selon le cercle du type de PII."""
    if pii_type in CERCLE_1:
        return ROSE_100
    if pii_type in CERCLE_2:
        return GOLD_100
    if pii_type in CERCLE_3:
        return TEAL_50
    return SILVER_100


# Couleurs, polices, arrondis et fond de la barre latérale sont gérés
# nativement par .streamlit/config.toml (Streamlit >= 1.66). Ce CSS ne garde
# que ce que le thème natif ne sait pas faire : accents or et composants maison.
# Les noms de police renvoient aux [[theme.fontFaces]] de config.toml.
_CSS = f"""
<style>
/* Titres en teal (le thème natif ne colore que le texte courant) */
h1, h2, h3, h4 {{ color: {TEAL_700} !important; }}

/* Bouton primaire : survol avec liseré or */
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover {{
    background: {TEAL_500} !important;
    border-color: {GOLD_500} !important;
}}
/* Bouton de téléchargement : accent or */
[data-testid="stDownloadButton"] button {{
    background: {GOLD_500} !important;
    color: {INK_900} !important;
    border: none !important;
    font-family: 'Poppins', sans-serif;
    font-weight: 500;
}}
[data-testid="stDownloadButton"] button:hover {{ background: #B8913A !important; }}

/* Barre latérale : liseré or */
[data-testid="stSidebar"] {{ border-right: 3px solid {GOLD_500}; }}

/* Métriques en carte */
[data-testid="stMetricValue"] {{ font-family: 'Poppins', sans-serif; color: {TEAL_700}; }}
[data-testid="stMetric"] {{
    background: #FFFFFF; border: 1px solid #E7E1D4; border-radius: 12px;
    padding: 12px 16px;
}}

/* Conteneurs à bordure : fond blanc */
[data-testid="stVerticalBlockBorderWrapper"] {{ background: #FFFFFF; border-radius: 12px; }}

/* Onglets : soulignement or */
.stTabs [aria-selected="true"] {{ color: {TEAL_700} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {GOLD_500} !important; }}

/* Bandeau de marque */
.anm-header {{
    display: flex; align-items: center; gap: 18px;
    padding: 18px 24px; margin: -40px 0 24px;
    background: {TEAL_700}; border-radius: 16px;
    border-bottom: 3px solid {GOLD_500};
}}
.anm-header svg {{ flex-shrink: 0; }}
.anm-header .anm-eyebrow {{
    font-family: 'Poppins', sans-serif; font-weight: 600; font-size: 12px;
    letter-spacing: 2px; text-transform: uppercase; color: {GOLD_500};
}}
.anm-header .anm-title {{
    font-family: 'Poppins', sans-serif; font-weight: 600;
    font-size: 26px; color: #FFFFFF; line-height: 1.2; margin-top: 2px;
}}
.anm-header .anm-sub {{ color: #CFE0DD; font-size: 14px; margin-top: 4px; }}

/* Marque compacte dans la barre latérale */
.anm-side {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
.anm-side .anm-name {{
    font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 20px; color: {TEAL_700};
}}

/* Texte affiché (original surligné ou caviardé) */
.anm-texte {{ white-space: pre-wrap; line-height: 2; color: {INK_900}; }}
.anm-texte mark {{ padding: 1px 4px; border-radius: 4px; color: {INK_900}; }}

.anm-jeton {{
    font-family: 'JetBrainsMono', monospace; font-size: 0.9em; font-weight: 500;
    padding: 1px 6px; border-radius: 4px;
    background: {GOLD_100}; color: {GOLD_700};
}}
.anm-tag {{
    display: inline-block; vertical-align: middle; margin-left: 4px;
    font-family: 'JetBrainsMono', monospace; font-size: 10.5px; font-weight: 500;
    padding: 1px 7px; border-radius: 999px;
    background: {GOLD_100}; color: {GOLD_700};
}}

/* Légende des cercles */
.anm-legende {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 2px 0 10px; }}
.anm-legende span {{
    font-family: 'JetBrainsMono', monospace; font-size: 11px; font-weight: 500;
    padding: 2px 9px; border-radius: 999px;
}}
/* Moins de marge vide en bas de page (évite une barre de défilement inutile) */
[data-testid="stMainBlockContainer"] {{ padding-bottom: 2rem; }}

/* Bandeau d'accueil : logo complet centré en haut de la page */
.anm-hero {{
    display: flex; flex-direction: column; align-items: center; text-align: center;
    margin: -48px 0 14px; padding: 0 4px 10px;
    border-bottom: 2px solid {GOLD_500};
}}
/* Taille liée à la hauteur de l'écran : la page de connexion tient sans défiler */
.anm-hero img, .anm-hero svg {{ height: clamp(100px, 20vh, 160px); width: auto; }}
.anm-hero .anm-sub {{ color: {INK_500}; font-size: 15px; margin-top: 6px; }}
</style>
"""


def _logo(taille: int) -> str:
    return f"""
<svg width="{taille}" height="{taille}" viewBox="0 0 104 104" aria-hidden="true">
  <circle cx="52" cy="52" r="50" fill="{TEAL_900}" stroke="{GOLD_500}" stroke-width="3"/>
  <path d="M52 24 L74 33 V54 C74 68 64 76 52 81 C40 76 30 68 30 54 V33 Z"
        fill="none" stroke="{GOLD_500}" stroke-width="3.4" stroke-linejoin="round"/>
  <rect x="42" y="50" width="20" height="17" rx="3" fill="{GOLD_500}"/>
  <path d="M45 50 v-5 a7 7 0 0 1 14 0 v5" fill="none" stroke="{GOLD_500}" stroke-width="3"/>
  <circle cx="52" cy="57" r="2.6" fill="{TEAL_900}"/>
  <rect x="50.6" y="58" width="2.8" height="5" rx="1.2" fill="{TEAL_900}"/>
</svg>"""


# Repère les jetons produits par le masquage : [EMAIL_1], [PHONE_NUMBER_2], [IP_V4_1]...
_JETON = re.compile(r"\[([A-Z][A-Z0-9_]*?)_(\d+)\]")


def apply_theme() -> None:
    """Injecte les styles complémentaires au thème natif. À appeler juste après st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title: str, description: str = "", eyebrow: str = "anonymia") -> None:
    """En-tête de page (une fois connecté) : bandeau teal portant le titre de l'écran.

    Le bandeau n'est plus un simple rappel de la marque : il sert de titre à
    la page, ce qui évite un bandeau isolé au-dessus d'un second titre.
    """
    desc = f'<div class="anm-sub">{html.escape(description)}</div>' if description else ""
    st.markdown(
        f'<div class="anm-header">{_logo(52)}<div>'
        f'<div class="anm-eyebrow">{html.escape(eyebrow)}</div>'
        f'<div class="anm-title">{html.escape(title)}</div>{desc}'
        f"</div></div>",
        unsafe_allow_html=True,
    )


# Logo complet (boîte de caviar + nom) : lu sur le disque à côté de ce fichier et intégré
# directement dans la page (base64). Ne dépend ni du dossier d'où Streamlit
# est lancé, ni du service de fichiers statiques.
LOGO_COMPLET = Path(__file__).resolve().parent / "static" / "anonymia_logo.png"


@st.cache_data
def _logo_complet_src() -> str | None:
    try:
        donnees = LOGO_COMPLET.read_bytes()
    except OSError:
        return None
    return "data:image/png;base64," + base64.b64encode(donnees).decode("ascii")


def hero_header(subtitle: str = "Caviardage de données personnelles dans les documents administratifs") -> None:
    """Accueil : logo complet centré en haut, puis le sous-titre (le nom est dans le logo)."""
    src = _logo_complet_src()
    if src is None:
        # Image absente : petit logo vectoriel + nom en texte, pour garder la marque.
        st.warning(f"Logo introuvable : {LOGO_COMPLET}")
        image = _logo(120) + '<div class="anm-name" style="font-family:Poppins,sans-serif;font-weight:700;font-size:44px;color:#0E3B38">anonymia</div>'
    else:
        image = f'<img src="{src}" alt="Anonymia">'
    st.markdown(
        f'<div class="anm-hero">{image}<div class="anm-sub">{html.escape(subtitle)}</div></div>',
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    """Marque compacte pour la barre latérale : petit logo rond + nom."""
    st.markdown(
        f'<div class="anm-side">{_logo(30)}<span class="anm-name">anonymia</span></div>',
        unsafe_allow_html=True,
    )

def legende_cercles() -> None:
    """Petite légende des couleurs de surlignage."""
    st.markdown(
        '<div class="anm-legende">'
        f'<span style="background:{ROSE_100};color:{ROSE_700}">Identifiants directs</span>'
        f'<span style="background:{GOLD_100};color:{GOLD_700}">Identifiants indirects</span>'
        f'<span style="background:{TEAL_50};color:{TEAL_700}">Données sensibles</span>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_redacted(text: str, show_labels: bool = True) -> str:
    """Texte caviardé en HTML : chaque jeton [TYPE_N] devient une barre de caviar.

    Le texte est échappé d'abord : un document contenant du HTML ne peut pas
    injecter de code dans la page. En pseudonymisation (pas de jetons),
    le texte est simplement affiché tel quel.
    """
    if not text:
        return '<div class="anm-texte"><em>Aucun contenu enregistré pour ce document.</em></div>'
    safe = html.escape(text.replace("\r", ""))

    def _barre(m: re.Match) -> str:
        pii_type = m.group(1)
        return f'<span class="anm-jeton" title="{pii_type}">{m.group(0)}</span>'

    return f'<div class="anm-texte">{_JETON.sub(_barre, safe)}</div>'