import os

from openai import AsyncOpenAI

from utils.env_variables import load_environment_variables

from .prompt_templates import SYSTEM_PROMPT, build_user_message

load_environment_variables()


async def detect_pii(document: str) -> str | None:
    client = AsyncOpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["SSPCLOUD_API_KEY"],
        timeout=60.0,
    )

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
