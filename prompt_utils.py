from __future__ import annotations


def build_messages(pdf_text: str, user_prompt: str):
    """
    Compose chat messages for the OpenAI API.
    """
    return [
        {
            "role": "system",
            "content": "Ты — ассистент, который отвечает, опираясь на текст PDF. Отвечай кратко и по делу.",
        },
        {
            "role": "user",
            "content": f"Текст PDF:\n{pdf_text}",
        },
        {
            "role": "user",
            "content": f"Инструкция пользователя: {user_prompt}",
        },
    ]


