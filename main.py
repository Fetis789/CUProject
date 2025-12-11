"""
Utility script to extract text from `grant_files/second_generated_grant.pdf`
and send it to OpenAI `gpt-4o-mini` together with a user-provided prompt.

Usage:
    OPENAI_API_KEY=... python main.py --prompt "Кратко резюмируй документ"

Dependencies are listed in `requirements.txt`.
"""
from __future__ import annotations

import argparse -u main.
import os
from pathlib import Path

from openai import OpenAI

from pdf_utils import extract_pdf_text
from prompt_utils import build_messages


def call_model(messages, model: str = "gpt-4o-mini", temperature: float = 0.2) -> str:
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
    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(
        description="Parse PDF and query gpt-4o-mini with the PDF content + user prompt."
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
        default="gpt-4o-mini",
        help="OpenAI chat model to use (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path(__file__).parent / "grant_files" / "second_generated_grant.pdf",
        help="Path to the PDF file.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the model (default: 0.2).",
    )
    args = parser.parse_args()

    pdf_path: Path = args.pdf
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pdf_text = extract_pdf_text(pdf_path)
    
    print(f'Начало текста: {pdf_text[:100]}')
    messages = build_messages(pdf_text, args.prompt)
    print('Вызываем модель...')
    reply = call_model(messages, model=args.model, temperature=args.temperature)
    print(reply)


if __name__ == "__main__":
    main()

