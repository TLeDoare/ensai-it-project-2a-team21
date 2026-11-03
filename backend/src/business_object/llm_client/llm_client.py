import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from .prompt_templates import SYSTEM_PROMPT, build_user_message

load_dotenv()

client = AsyncOpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["SSPCLOUD_API_KEY"],
    timeout=60.0,
)


async def detect_pii(document: str) -> str | None:
    response = await client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "qwen3-6-35b-moe"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(document)},
        ],
        temperature=0.1,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import asyncio

    exemple = ("Monsieur Pierre Dupont, domicilié 12 rue de la Paix, 75002 Paris, "
               "a déposé sa demande le 3 mars 2025.")
    print(asyncio.run(detect_pii(exemple)))