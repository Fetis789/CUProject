from __future__ import annotations

from pathlib import Path
from typing import Optional

# Кэш для рекомендаций (загружаются один раз)
_GRANT_RULES_CACHE: Optional[str] = None


def _load_grant_rules() -> str:
    """
    Загружает рекомендации по оформлению заявок из файла.
    Кэширует результат для последующих вызовов.
    """
    global _GRANT_RULES_CACHE
    
    if _GRANT_RULES_CACHE is not None:
        return _GRANT_RULES_CACHE
    
    rules_path = Path(__file__).parent / "parsed_texts" / "rules_grant.txt"
    
    if rules_path.exists():
        try:
            _GRANT_RULES_CACHE = rules_path.read_text(encoding="utf-8").strip()
            return _GRANT_RULES_CACHE
        except Exception as e:
            # Если не удалось загрузить, возвращаем пустую строку
            print(f"Предупреждение: не удалось загрузить рекомендации из {rules_path}: {e}")
            _GRANT_RULES_CACHE = ""
            return ""
    else:
        # Файл не найден - возвращаем пустую строку
        _GRANT_RULES_CACHE = ""
        return ""


def build_messages(pdf_text: str, user_prompt: str):
    """
    Compose chat messages for the OpenAI API.
    Автоматически включает рекомендации по оформлению заявок в системный промпт.
    """
    # Загружаем рекомендации
    grant_rules = _load_grant_rules()
    
    # Формируем системный промпт
    system_content = "Ты — ассистент, который отвечает, опираясь на текст PDF. Отвечай кратко и по делу."

    system_content += "\n\nВАЖНО: В случае построения таблиц выводи их в формате markdown, а не в виде текста."
    
    # Добавляем рекомендации, если они загружены
    if grant_rules:
        system_content += f"\n\nВАЖНО: При оценке заявок ты ДОЛЖЕН учитывать следующие рекомендации по оформлению заявок:\n\n{grant_rules}"
    
    return [
        {
            "role": "system",
            "content": system_content,
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







