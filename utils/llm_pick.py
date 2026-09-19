import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def pick_llm(level: str):
    """Return a safe OmniRoute-compatible ChatOpenAI client.

    The OmniRoute gateway accepts OpenAI-compatible parameters, but it can reject
    unsupported fields like reasoning_effort when model aliases are used.
    """
    level_lower = level.lower()
    model_map = {
        "low": os.getenv("OPENAI_MODEL_LOW", "nvidia/openai/gpt-oss-20b"),
        "medium": os.getenv("OPENAI_MODEL_MEDIUM", "nvidia/openai/gpt-oss-20b"),
        "high": os.getenv("OPENAI_MODEL_HIGH", "nvidia/nvidia/nemotron-3-super-120b-a12b"),
    }

    if level_lower not in model_map:
        raise ValueError(f"Unsupported Level : {level}")

    config = {
        "model": model_map[level_lower],
        "temperature": 0,
    }

    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if base_url:
        config["base_url"] = base_url
    if api_key:
        config["api_key"] = api_key

    return ChatOpenAI(**config)
