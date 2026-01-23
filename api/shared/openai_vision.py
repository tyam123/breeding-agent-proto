# /api/shared/openai_vision.py
import os, json, base64, requests

def _b64_jpeg(img_bytes: bytes) -> str:
    return base64.b64encode(img_bytes).decode("utf-8")

def call_openai_vision(system_text: str, user_text: str, img_bytes: bytes) -> str:
    api_key = os.environ["OPENAI_API_KEY"]
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # Chat Completions互換の形で送る（modelは差し替え前提）
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{_b64_jpeg(img_bytes)}"}}
            ]}
        ],
        "temperature": 0,
    }

    r = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=120,
    )
    r.raise_for_status()
    txt = r.json()["choices"][0]["message"]["content"]
    return txt
