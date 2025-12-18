"""
FastAPI server for PDF processing with OpenAI.

Endpoints:
    POST /upload - Upload PDF file and start processing
    GET /result/{task_id} - Get processing result by task ID
    GET /health - Health check endpoint

Usage:
    OPENAI_API_KEY=... uvicorn api_server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from openai import OpenAI

from pdf_utils import extract_pdf_text
from prompt_utils import build_messages
from dotenv import load_dotenv 

load_dotenv()

app = FastAPI(title="PDF Processing API", version="1.0.0")

# In-memory storage for task results
# In production, use a proper database or cache (Redis, etc.)
task_results: Dict[str, Dict] = {}

# Temporary directory for uploaded files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


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
def call_model(messages, model: str = "openai/gpt-4o", temperature: float = 0.2) -> str:
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

    # Увеличенный таймаут для больших PDF и сложных промптов
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        timeout=300,  # 5 минут таймаут для API вызова
        # Примечание: некоторые модели/провайдеры в OpenRouter могут не поддерживать temperature.
        # Если словишь 400 — попробуй убрать temperature полностью.
        # temperature=0.2,
    )

    return response.choices[0].message.content


async def process_pdf_task(
    task_id: str,
    pdf_path: Path,
    prompt: str,
    model: str = "openai/gpt-4o",
    temperature: float = 0.2,
    organization: str = "ФПИ",
):
    """
    Asynchronously process PDF file and store result.
    """
    try:
        # Update task status
        task_results[task_id]["status"] = "processing"
        task_results[task_id]["message"] = "Extracting text from PDF..."

        # Extract text from PDF
        pdf_text = extract_pdf_text(pdf_path)

        # Update status
        task_results[task_id]["message"] = "Calling OpenAI API..."

        # Build messages and call model
        messages = build_messages(pdf_text, prompt, organization=organization)
        result = call_model(messages, model=model, temperature=temperature)

        # Store result
        task_results[task_id]["status"] = "completed"
        task_results[task_id]["result"] = result
        task_results[task_id]["message"] = "Processing completed successfully"

        # Clean up uploaded file
        if pdf_path.exists():
            pdf_path.unlink()

    except Exception as e:
        task_results[task_id]["status"] = "error"
        task_results[task_id]["error"] = str(e)
        task_results[task_id]["message"] = f"Error during processing: {str(e)}"

        # Clean up uploaded file on error
        if pdf_path.exists():
            pdf_path.unlink()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "API is running"}


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to process"),
    prompt: Optional[str] = Form(
        default="Сделай краткую суммаризацию проекта, представленного в документе.",
        description="User prompt for the model",
    ),
    model: Optional[str] = Form(
        default="openai/gpt-4o", description="OpenAI model to use"
    ),
    temperature: Optional[float] = Form(
        default=0.2, description="Sampling temperature (0.0-2.0)"
    ),
    organization: Optional[str] = Form(
        default="ФПИ", description="Организация: 'ФПИ' или 'ЦУ'"
    ),
):
    """
    Upload PDF file and start processing.

    Returns task_id that can be used to retrieve results via GET /result/{task_id}
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Save uploaded file
    file_path = UPLOAD_DIR / f"{task_id}.pdf"
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Initialize task result
    task_results[task_id] = {
        "status": "pending",
        "message": "Task created, waiting to start processing",
        "result": None,
        "error": None,
    }

    # Validate organization parameter
    if organization not in ["ФПИ", "ЦУ"]:
        raise HTTPException(
            status_code=400, 
            detail="organization must be either 'ФПИ' or 'ЦУ'"
        )

    # Start async processing
    asyncio.create_task(
        process_pdf_task(task_id, file_path, prompt, model, temperature, organization)
    )

    return JSONResponse(
        status_code=202,
        content={
            "task_id": task_id,
            "status": "pending",
            "message": "File uploaded successfully, processing started",
        },
    )


@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """
    Get processing result by task ID.

    Returns:
        - If status is "completed": returns the result
        - If status is "processing": returns current status
        - If status is "error": returns error message
        - If task_id not found: returns 404
    """
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = task_results[task_id]

    if task_data["status"] == "completed":
        return {
            "task_id": task_id,
            "status": "completed",
            "result": task_data["result"],
        }
    elif task_data["status"] == "error":
        return {
            "task_id": task_id,
            "status": "error",
            "error": task_data.get("error", "Unknown error"),
            "message": task_data.get("message", ""),
        }
    else:
        return {
            "task_id": task_id,
            "status": task_data["status"],
            "message": task_data.get("message", "Processing in progress"),
        }


@app.get("/tasks")
async def list_tasks():
    """
    List all tasks with their statuses.
    """
    return {
        "tasks": [
            {
                "task_id": task_id,
                "status": data["status"],
                "message": data.get("message", ""),
            }
            for task_id, data in task_results.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn

    # Для локального тестирования: host="0.0.0.0" или "127.0.0.1" или "localhost"
    # host="0.0.0.0" позволяет принимать подключения со всех интерфейсов (включая localhost)
    uvicorn.run(app, host="0.0.0.0", port=8000)




