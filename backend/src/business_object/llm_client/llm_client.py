import json
import os

from llm_client.prompt_templates import SYSTEM_PROMPT, build_user_message
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["SSPCLOUD_API_KEY"],
)


async def detect_pii(document: str) -> list:
    response = await client.chat.completions.create(
        model="llama3.1:8b",
        messages=[
          {"role": "system", "content": SYSTEM_PROMPT},
          {"role": "user", "content": build_user_message(document)},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    return json.loads(raw)["spans"]
