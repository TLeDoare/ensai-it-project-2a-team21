import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["SSPCLOUD_API_KEY"],
)

r = client.chat.completions.create(
    model="qwen3-6-35b-moe",
    messages=[
        {"role": "user", "content": "fourni un petit code"},
    ],
    temperature=0.1,
    max_tokens=1000,
)

choix = r.choices[0]
print("Raison d'arrêt :", choix.finish_reason)
print("Réponse :", choix.message.content)