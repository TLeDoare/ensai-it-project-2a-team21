import os

from openai import AsyncOpenAI

from utils.env_variables import load_environment_variables

from .prompt_templates import (
    JUDGE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_judge_message,
    build_rewrite_message,
    build_rewrite_system_prompt,
    build_user_message,
)

load_environment_variables()

# on doit encapsuler cela dans une fonction pour qu'il soit:
# 1) non executé dans le cas où ne veut pas utiliser le LLM
# 2) mocké dans les tests qui ont besoin d'accéder à AsyncOpenAI
def create_client():
    return AsyncOpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["SSPCLOUD_API_KEY"],
        timeout=120.0,
    )

async def detect_pii(document: str) -> str | None:
    client = create_client()

    response = await client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gemma4-26b-moe"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(document)},
        ],
        temperature=0.1,
        max_tokens=8000,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


async def anonymiser_directement(document: str, masquer: bool = True) -> str:
    """FO2 : le LLM renvoie directement le document anonymisé (texte libre, pas de JSON).

    masquer=True : marqueurs [NAME_1]... ; masquer=False : données fictives (pseudonymisation).
    """
    client = create_client()

    response = await client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gemma4-26b-moe"),
        messages=[
            {"role": "system", "content": build_rewrite_system_prompt(masquer)},
            {"role": "user", "content": build_rewrite_message(document)},
        ],
        temperature=0.1,
        max_tokens=8000,
    )
    return response.choices[0].message.content or ""


async def juger_injection(document: str) -> str:
    """FO3 : demande au LLM si le document tente de manipuler le système ; renvoie son JSON brut."""
    client = create_client()

    response = await client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gemma4-26b-moe"),
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": build_judge_message(document)},
        ],
        temperature=0.0,
        max_tokens=50,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content
