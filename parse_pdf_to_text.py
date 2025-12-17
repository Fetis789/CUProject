"""
Парсинг PDF файла в текстовый файл.

Скрипт обрабатывает один PDF файл и сохраняет извлеченный текст
в папку 'parsed_texts/' с тем же названием.

Использование:
    python parse_pdf_to_text.py file.pdf
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pdf_utils import extract_pdf_text


def main():
    """Основная функция для парсинга одного PDF файла."""
    parser = argparse.ArgumentParser(
        description="Парсит PDF файл и сохраняет текст в текстовый файл."
    )
    parser.add_argument(
        "pdf_file",
        type=Path,
        help="Путь к PDF файлу для обработки",
    )
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_file)
    
    # Проверяем существование файла
    if not pdf_path.exists():
        print(f"✗ Файл не найден: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    
    if not pdf_path.suffix.lower() == ".pdf":
        print(f"✗ Указанный файл не является PDF: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    
    # Определяем выходную папку
    script_dir = Path(__file__).parent
    output_dir = script_dir / "parsed_texts"
    
    # Создаем выходную папку, если её нет
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Извлекаем текст из PDF
        print(f"Обработка файла: {pdf_path.name}...")
        text = extract_pdf_text(pdf_path)
        
        # Создаем имя выходного файла (то же имя, но .txt)
        output_filename = pdf_path.stem + ".txt"
        output_path = output_dir / output_filename
        
        # Сохраняем текст в файл
        output_path.write_text(text, encoding="utf-8")
        
        print(f"✓ Успешно обработан: {pdf_path.name}")
        print(f"✓ Результат сохранен: {output_path}")
        
    except Exception as e:
        print(f"✗ Ошибка при обработке {pdf_path.name}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

