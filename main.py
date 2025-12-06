from litellm_utils import request_ai
from pathlib import Path

def generate_mark_scheme(file: str | Path):
    system_prompt = """You're an expert mark scheme creator
    """

    response = request_ai(
        provider="gemini",
        model="gemini-3-pro-preview",
        system_prompt="",
        file=file
    )

    return response

print(generate_mark_scheme("past_papers/2017281-INFR08018.pdf"))