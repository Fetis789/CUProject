"""
Utility script to extract text from `grant_files/second_generated_grant.pdf`
and send it to OpenAI `gpt-4o-mini` together with a user-provided prompt.

Usage:
    OPENAI_API_KEY=... python main.py --prompt "Кратко резюмируй документ"

Dependencies are listed in `requirements.txt`.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from openai import OpenAI

from pdf_utils import extract_pdf_text
from prompt_utils import build_messages
from dotenv import load_dotenv 

load_dotenv()


'''def call_model(messages, model: str = "gpt-5-mini", temperature: float = 0.2) -> str:
    """
    Call the OpenAI chat completion API and return the assistant reply text.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content'''

#Вариант через Openrouter
def call_model(messages, model: str = "openai/gpt-5") -> str:
    """
    Call OpenRouter (OpenAI-compatible) chat completion API and return assistant reply text.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in the environment.")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        # Рекомендуемые OpenRouter заголовки (идентификация приложения)
        default_headers={
            "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://cu-grant-analyzis-project.onrender.com"),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "CU Grant Analysis Project"),
        },
    )

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        # Примечание: некоторые модели/провайдеры в OpenRouter могут не поддерживать temperature.
        # Если словишь 400 — попробуй убрать temperature полностью.
        # temperature=0.2,
    )

    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(
        description="Parse PDF and query gpt-5 with the PDF content + user prompt."
    )
    parser.add_argument(
        "--prompt",
        "-p",
        default="Сделай краткую суммаризацию проекта, представленного в документе.",
        required=False,
        help="User prompt to pass to the model (e.g., 'Кратко резюмируй документ').",
    )
    parser.add_argument(
        "--model",
        default="openai/gpt-5",
        help="OpenAI chat model to use (default: gpt-5).",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path(__file__).parent / "grant_files" / "second_generated_grant.pdf",
        help="Path to the PDF file.",
    )

    #Температуру в итоге убрали
    '''parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the model (default: 0.2).",
    )'''

    args = parser.parse_args()

    pdf_path: Path = args.pdf
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pdf_text = extract_pdf_text(pdf_path)
    
    print(f'Начало текста: {pdf_text[:100]}')
    messages = build_messages(pdf_text, args.prompt)
    print('Вызываем модель...')
    reply = call_model(messages, model=args.model)
    print(reply)


if __name__ == "__main__":
    main()

