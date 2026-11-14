import os

from openai import AsyncOpenAI

from utils.env_variables import load_environment_variables

from .prompt_templates import SYSTEM_PROMPT, build_user_message

load_environment_variables()

# on doit encapsuler cela dans une fonction pour qu'il soit:
# 1) non executé dans le cas où ne veut pas utiliser le LLM
# 2) mocké dans les tests qui ont besoin d'accéder à AsyncOpenAI
def create_client():
    return AsyncOpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["SSPCLOUD_API_KEY"],
        timeout=60.0,
    )

async def detect_pii(document: str) -> str | None:
    client = create_client()

    response = await client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "qwen3-6-35b-moe"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(document)},
        ],
        temperature=0.1,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content
