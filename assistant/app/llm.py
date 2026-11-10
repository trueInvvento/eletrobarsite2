from openai import OpenAI

from app.config import get_settings


def get_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    client = get_client()
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
    )
    return response.data[0].embedding


def embed_batch(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    client = get_client()
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


def chat_completion(system: str, messages: list[dict[str, str]]) -> str:
    settings = get_settings()
    client = get_client()
    payload = [{"role": "system", "content": system}, *messages]
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=payload,
        temperature=0.4,
    )
    return response.choices[0].message.content or ""
