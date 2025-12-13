# PDF Processing API

REST API для обработки PDF файлов с помощью OpenAI GPT-4o-mini.

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Установите переменную окружения:
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

## Запуск сервера

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

Или через Python:
```bash
python api_server.py
```

Сервер будет доступен по адресу: `https://cu-grant-analyzis-project.onrender.com/`

## API Endpoints

### 1. Health Check
**GET** `/health`

Проверка работоспособности API.

**Ответ:**
```json
{
  "status": "ok",
  "message": "API is running"
}
```

### 2. Загрузка PDF и начало обработки
**POST** `/upload`

Загружает PDF файл и запускает асинхронную обработку.

**Параметры:**
- `file` (form-data, file): PDF файл для обработки
- `prompt` (form-data, string, опционально): Промпт для модели (по умолчанию: "Сделай краткую суммаризацию проекта, представленного в документе.")
- `model` (form-data, string, опционально): Модель OpenAI (по умолчанию: "gpt-4o-mini")
- `temperature` (form-data, float, опционально): Температура выборки (по умолчанию: 0.2)

**Ответ:**
```json
{
  "task_id": "uuid-here",
  "status": "pending",
  "message": "File uploaded successfully, processing started"
}
```

**Пример запроса (curl):**
```bash
curl -X POST "https://cu-grant-analyzis-project.onrender.com/upload" \
  -F "file=@path/to/file.pdf" \
  -F "prompt=Кратко резюмируй документ" \
  -F "model=gpt-4o-mini" \
  -F "temperature=0.2"
```

**Пример запроса (Python requests):**
```python
import requests

url = "https://cu-grant-analyzis-project.onrender.com/upload"
files = {"file": open("document.pdf", "rb")}
data = {
    "prompt": "Кратко резюмируй документ",
    "model": "gpt-4o-mini",
    "temperature": 0.2
}
response = requests.post(url, files=files, data=data)
print(response.json())
```

### 3. Получение результата обработки
**GET** `/result/{task_id}`

Получает результат обработки по ID задачи.

**Параметры:**
- `task_id` (path): ID задачи, полученный при загрузке файла

**Ответы:**

Если обработка завершена:
```json
{
  "task_id": "uuid-here",
  "status": "completed",
  "result": "Результат обработки модели..."
}
```

Если обработка в процессе:
```json
{
  "task_id": "uuid-here",
  "status": "processing",
  "message": "Calling OpenAI API..."
}
```

Если произошла ошибка:
```json
{
  "task_id": "uuid-here",
  "status": "error",
  "error": "Error message here",
  "message": "Error during processing: ..."
}
```

**Пример запроса:**
```bash
curl "https://cu-grant-analyzis-project.onrender.com/result/{task_id}"
```

### 4. Список всех задач
**GET** `/tasks`

Получает список всех задач с их статусами.

**Ответ:**
```json
{
  "tasks": [
    {
      "task_id": "uuid-1",
      "status": "completed",
      "message": "Processing completed successfully"
    },
    {
      "task_id": "uuid-2",
      "status": "processing",
      "message": "Calling OpenAI API..."
    }
  ]
}
```

## Документация API

После запуска сервера доступна интерактивная документация:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Пример использования

1. Запустите сервер:
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

2. Загрузите PDF файл:
```bash
curl -X POST "https://cu-grant-analyzis-project.onrender.com/upload" \
  -F "file=@grant_files/second_generated_grant.pdf" \
  -F "prompt=Сделай краткую суммаризацию проекта"
```

3. Получите task_id из ответа и проверьте результат:
```bash
curl "https://cu-grant-analyzis-project.onrender.com/result/{task_id}"
```

4. Повторяйте шаг 3, пока статус не станет "completed" или "error".

## Примечания

- Загруженные файлы временно сохраняются в папке `uploads/` и автоматически удаляются после обработки
- Результаты задач хранятся в памяти (при перезапуске сервера теряются)
- Для production рекомендуется использовать базу данных или кэш (Redis) для хранения результатов

