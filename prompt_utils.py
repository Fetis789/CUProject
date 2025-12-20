from __future__ import annotations

from pathlib import Path
from typing import Optional

# Кэш для рекомендаций (загружаются один раз для каждой организации)
_GRANT_RULES_CACHE: dict[str, str] = {}


def _load_grant_rules(organization: str = "ФПИ") -> str:
    """
    Загружает рекомендации по оформлению заявок из файла в зависимости от организации.
    Кэширует результат для последующих вызовов.
    
    Args:
        organization: Организация ("ФПИ" или "ЦУ")
    
    Returns:
        Текст рекомендаций или пустая строка, если файл не найден
    """
    global _GRANT_RULES_CACHE
    
    # Проверяем кэш
    if organization in _GRANT_RULES_CACHE:
        return _GRANT_RULES_CACHE[organization]
    
    # Определяем путь к файлу в зависимости от организации
    if organization == "ФПИ":
        rules_filename = "rules_grant.txt"
    elif organization == "ЦУ":
        rules_filename = "cu_rules.txt"
    else:
        print(f"Предупреждение: неизвестная организация '{organization}'. Используется ФПИ.")
        rules_filename = "rules_grant.txt"
    
    rules_path = Path(__file__).parent / "parsed_texts" / rules_filename
    
    if rules_path.exists():
        try:
            rules_text = rules_path.read_text(encoding="utf-8").strip()
            _GRANT_RULES_CACHE[organization] = rules_text
            return rules_text
        except Exception as e:
            # Если не удалось загрузить, возвращаем пустую строку
            print(f"Предупреждение: не удалось загрузить рекомендации из {rules_path}: {e}")
            _GRANT_RULES_CACHE[organization] = ""
            return ""
    else:
        # Файл не найден - возвращаем пустую строку
        print(f"Предупреждение: файл рекомендаций не найден: {rules_path}")
        _GRANT_RULES_CACHE[organization] = ""
        return ""


def build_messages(pdf_text: str, user_prompt: str, organization: str = "ФПИ"):
    """
    Compose chat messages for the OpenAI API.
    Автоматически включает рекомендации по оформлению заявок в системный промпт.
    
    Args:
        pdf_text: Текст из PDF файла
        user_prompt: Промпт пользователя
        organization: Организация ("ФПИ" или "ЦУ"). По умолчанию "ФПИ"
    """
    # Загружаем рекомендации в зависимости от организации
    grant_rules = _load_grant_rules(organization=organization)
    
    # Формируем системный промпт
    system_content = "Ты — ассистент, который отвечает, опираясь на текст PDF. Отвечай кратко и по делу."

    #system_content += "\n\nВАЖНО: Весь свой ответ выводи в формате, подходящем для Markdown."
    #system_content += "\n\nВАЖНО: Для таблиц используй правильный формат Markdown:"
    
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







