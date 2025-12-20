import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from dotenv import load_dotenv 

load_dotenv()

import pandas as pd
import requests
from requests.exceptions import Timeout, RequestException
import streamlit as st

#API_URL = os.getenv("API_URL", "https://cu-grant-analyzis-project.onrender.com")
API_URL = "http://localhost:8000"



@dataclass
class TaskItem:
    filename: str
    task_id: str
    status: str = "pending"
    message: str = ""
    result: Optional[str] = None
    error: Optional[str] = None



def api_health() -> bool:
    try:
        # Увеличенный таймаут для Render (может быть cold start)
        r = requests.get(f"{API_URL}/health", timeout=30)
        return r.status_code == 200
    except Exception:
        return False


def api_upload_pdf(pdf_bytes: bytes, filename: str, prompt: str, model: str, temperature: float, organization: str = "ФПИ", pdf_type: str = "application") -> str:
    files = {"file": (filename, pdf_bytes, "application/pdf")}
    data = {
        "prompt": prompt, 
        "model": model, 
        "temperature": str(temperature),
        "organization": organization,
        "pdf_type": pdf_type
    }
    # Увеличенный таймаут для загрузки больших файлов на Render
    r = requests.post(f"{API_URL}/upload", files=files, data=data, timeout=180)
    r.raise_for_status()
    return r.json()["task_id"]


def api_get_result(task_id: str) -> Dict:
    # Увеличенный таймаут для Render (может быть медленным из-за cold start)
    r = requests.get(f"{API_URL}/result/{task_id}", timeout=120)
    r.raise_for_status()
    return r.json()


def build_prompt_from_form(cfg: Dict) -> str:
    out_format = """\
Верни ответ СТРОГО в формате:
1) Краткое резюме (5-7 буллетов)
2) Соответствие проекта рекомендациям по оформлению заявок (да/нет + объяснение), которые были выданы тебе ранее. Уточни, в каких моментах есть нессответствие, если оно есть.
3) Сильные стороны (3-5 буллетов)
4) Риски/красные флаги (3-5 буллетов)
5) Ответы по критериям эксперта - ОБЯЗАТЕЛЬНО в формате таблицы, которая будет конвертироваться в Markdown:
Таблица ДОЛЖНА быть в формате Markdown без пустых строк внутри:
| Критерий | Оценка | Обоснование |
| --- | --- | --- |
| Техническая реализуемость | Средняя | Есть описанная архитектура и CJM; доступны готовые LLM и Nikta Graph; понятные модули UI и бэкенда; нет прототипа и результатов тестов; не проработаны метрики качества и защита данных |
ВАЖНО: 
- Каждая строка таблицы на отдельной строке
- НЕ используй переносы строк внутри ячеек
- Аргументы разделяй точкой с запятой и пробелом (; )
- Используй ТОЛЬКО формат таблицы Markdown, никаких других форматов
6) Рекомендация (поддержать / отклонить / на доработку) + почему
"""

    criteria_lines = "\n".join([f"- {c.strip()}" for c in cfg.get("criteria_list", []) if c.strip()])
    red_flags = "\n".join([f"- {c.strip()}" for c in cfg.get("red_flags", []) if c.strip()])

    prompt = f"""\
Ты помогаешь эксперту оценивать грантовые заявки.

Контекст конкурса (кратко, что важно учитывать):
{cfg.get("contest_notes","").strip()}

Критерии, по которым эксперт принимает решение:
{criteria_lines if criteria_lines.strip() else "- (не задано)"}

Красные флаги (если есть):
{red_flags if red_flags.strip() else "- (не задано)"}

Особые инструкции эксперта:
{cfg.get("special_instructions","").strip()}

{out_format}
"""
    return prompt


def ensure_state():
    if "prompt_cfg" not in st.session_state:
        st.session_state.prompt_cfg = {
            "contest_notes": "",
            "criteria_list": [],
            "red_flags": [],
            "special_instructions": "",
        }
    if "generated_prompt" not in st.session_state:
        st.session_state.generated_prompt = ""
    if "tasks" not in st.session_state:
        st.session_state.tasks: List[TaskItem] = []
    if "decisions" not in st.session_state:
        st.session_state.decisions = {}  # task_id -> {"decision":..., "comment":...}


# UI
st.set_page_config(page_title="Grant Expert Copilot (MVP)", layout="wide")
ensure_state()

st.title("Grant Expert Copilot (MVP)")

with st.sidebar:
    st.subheader("Подключение к бэку")
    st.write(f"API_URL: `{API_URL}`")
    ok = api_health()
    st.success("API доступен ✅" if ok else "API недоступен ❌")

    st.divider()
    st.subheader("Параметры модели")
    model_options = [
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/gpt-4-turbo",
        "openai/gpt-3.5-turbo",
        "openai/gpt-5"
    ]
    model = st.selectbox("Model", options=model_options, index=0)
    temperature = st.slider("Temperature", 0.0, 1.5, 0.2, 0.05)
    
    st.divider()
    st.subheader("Организация и тип документа")
    organization = st.selectbox("Организация", options=["ФПИ", "ЦУ"], index=0)
    pdf_type_display = st.selectbox("Тип документа", options=["Заявка", "Презентация"], index=0)
    # Маппинг: "Заявка" -> "application", "Презентация" -> "presentation"
    pdf_type = "application" if pdf_type_display == "Заявка" else "presentation"

tabs = st.tabs(["1) Настройка эксперта", "2) Загрузка PDF", "3) Очередь / результаты"])


# ----------------------------
# Tab 1: Expert setup
# ----------------------------
with tabs[0]:
    st.header("1) Настройка эксперта и конкурса")

    colA, colB = st.columns([1, 1], gap="large")

    with colA:
        st.subheader("Конкурсная документация")
        contest_doc = st.file_uploader("Загрузить конкурсную документацию (PDF/TXT) (опционально)", type=["pdf", "txt"])
        contest_link = st.text_input("…или ссылка на конкурсную документацию (опционально)", value="")

        notes = st.text_area(
            "Коротко: что главное в конкурсной документации (можно вставить выдержки/тезисы)",
            value=st.session_state.prompt_cfg["contest_notes"],
            height=180,
        )
        st.session_state.prompt_cfg["contest_notes"] = notes

        if contest_doc is not None:
            st.info("В MVP конкурсную документацию не парсим и не отправляем на бэк — используем как контекст в промпте.")
        if contest_link.strip():
            st.caption("Ссылка сохранена (как контекст).")

    with colB:
        st.subheader("Опросник: критерии эксперта")

        criteria_text = st.text_area(
            "Критерии (по одному в строке)",
            value="\n".join(st.session_state.prompt_cfg["criteria_list"]),
            height=160,
            placeholder="Напр.: Техническая реализуемость\nКоманда и компетенции\nБюджет обоснован\nСоответствие целям конкурса",
        )
        red_flags_text = st.text_area(
            "Красные флаги (по одному в строке)",
            value="\n".join(st.session_state.prompt_cfg["red_flags"]),
            height=120,
            placeholder="Напр.: Нет KPI\nНереалистичный срок\nБюджет без сметы",
        )
        special = st.text_area(
            "Особые инструкции (тональность, приоритеты, что считать критичным)",
            value=st.session_state.prompt_cfg["special_instructions"],
            height=120,
        )

        st.session_state.prompt_cfg["criteria_list"] = [x for x in criteria_text.splitlines()]
        st.session_state.prompt_cfg["red_flags"] = [x for x in red_flags_text.splitlines()]
        st.session_state.prompt_cfg["special_instructions"] = special

        if st.button("Сгенерировать инструкцию (prompt)"):
            st.session_state.generated_prompt = build_prompt_from_form(st.session_state.prompt_cfg)

    st.subheader("Итоговая инструкция для модели (user_prompt)")
    st.session_state.generated_prompt = st.text_area(
        "Можно вручную править перед запуском",
        value=st.session_state.generated_prompt,
        height=220,
    )


# ----------------------------
# Tab 2: Upload PDFs
# ----------------------------
with tabs[1]:
    st.header("2) Загрузка заявок (PDF)")

    pdf_files = st.file_uploader(
        "Загрузите один или несколько PDF",
        type=["pdf"],
        accept_multiple_files=True,
    )

    st.write(f"Сейчас в очереди: **{len(st.session_state.tasks)}** задач(и)")

    can_run = bool(pdf_files) and st.session_state.generated_prompt.strip() and ok
    st.caption("Нужны: PDF(ы) + сгенерированный prompt + доступный API.")

    if st.button("🚀 Запустить обработку PDF", disabled=not can_run):
        created: List[TaskItem] = []
        progress = st.progress(0)

        for i, f in enumerate(pdf_files, start=1):
            try:
                task_id = api_upload_pdf(
                    pdf_bytes=f.getvalue(),
                    filename=f.name,
                    prompt=st.session_state.generated_prompt,
                    model=model,
                    temperature=temperature,
                    organization=organization,
                    pdf_type=pdf_type,
                )
                created.append(TaskItem(filename=f.name, task_id=task_id))
            except Timeout:
                created.append(TaskItem(
                    filename=f.name, 
                    task_id="—", 
                    status="error", 
                    error="Таймаут при загрузке. Сервер может быть занят или перегружен. Попробуйте позже."
                ))
            except RequestException as e:
                created.append(TaskItem(
                    filename=f.name, 
                    task_id="—", 
                    status="error", 
                    error=f"Ошибка сети при загрузке: {str(e)}"
                ))
            except Exception as e:
                created.append(TaskItem(filename=f.name, task_id="—", status="error", error=str(e)))

            progress.progress(i / len(pdf_files))

        st.session_state.tasks.extend([t for t in created if t.task_id != "—"])

        st.success("Задачи созданы.")
        st.dataframe(pd.DataFrame([t.__dict__ for t in created]), use_container_width=True)


# ----------------------------
# Tab 3: Queue / results + decisions
# ----------------------------
with tabs[2]:
    st.header("3) Очередь / результаты")

    if not st.session_state.tasks:
        st.info("Пока нет задач. Перейдите на вкладку 'Загрузка PDF'.")
    else:
        colL, colR = st.columns([1, 1], gap="large")

        with colL:
            if st.button("🔄 Обновить статусы"):
                for t in st.session_state.tasks:
                    if t.task_id and t.task_id != "—" and t.status not in ("completed", "error"):
                        try:
                            payload = api_get_result(t.task_id)
                            t.status = payload.get("status", t.status)
                            t.message = payload.get("message", "")
                            if t.status == "completed":
                                t.result = payload.get("result")
                            if t.status == "error":
                                t.error = payload.get("error", "Unknown error")
                        except Timeout:
                            # Не меняем статус на error при таймауте - возможно, обработка еще идет
                            t.message = "Таймаут запроса. Сервер может быть занят. Попробуйте обновить позже."
                        except RequestException as e:
                            t.status = "error"
                            t.error = f"Ошибка сети: {str(e)}"
                        except Exception as e:
                            t.status = "error"
                            t.error = str(e)

            auto_poll = st.checkbox("Авто-обновление (каждые 3 сек)", value=False)
            if auto_poll:
                # короткий безопасный поллинг без бесконечного цикла
                for _ in range(3):
                    any_pending = any(t.status in ("pending", "processing") for t in st.session_state.tasks)
                    if not any_pending:
                        break
                    for t in st.session_state.tasks:
                        if t.status in ("pending", "processing"):
                            try:
                                payload = api_get_result(t.task_id)
                                t.status = payload.get("status", t.status)
                                t.message = payload.get("message", "")
                                if t.status == "completed":
                                    t.result = payload.get("result")
                                if t.status == "error":
                                    t.error = payload.get("error", "Unknown error")
                            except Timeout:
                                # Не меняем статус на error при таймауте - возможно, обработка еще идет
                                t.message = "Таймаут запроса. Сервер может быть занят."
                            except RequestException as e:
                                t.status = "error"
                                t.error = f"Ошибка сети: {str(e)}"
                            except Exception as e:
                                t.status = "error"
                                t.error = str(e)
                    time.sleep(3)
                st.rerun()

        with colR:
            st.subheader("Экспорт решений")
            rows = []
            for t in st.session_state.tasks:
                d = st.session_state.decisions.get(t.task_id, {})
                rows.append({
                    "filename": t.filename,
                    "task_id": t.task_id,
                    "status": t.status,
                    "decision": d.get("decision", ""),
                    "expert_comment": d.get("comment", ""),
                })
            df = pd.DataFrame(rows)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Скачать CSV", data=csv, file_name="expert_decisions.csv", mime="text/csv")

        st.subheader("Список заявок")
        table = pd.DataFrame([{
            "filename": t.filename,
            "task_id": t.task_id,
            "status": t.status,
            "message": t.message,
        } for t in st.session_state.tasks])
        st.dataframe(table, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Просмотр и решение по конкретной заявке")

        task_ids = [t.task_id for t in st.session_state.tasks]
        selected_id = st.selectbox("Выберите задачу", options=task_ids)
        selected = next(t for t in st.session_state.tasks if t.task_id == selected_id)

        left, right = st.columns([1, 1], gap="large")

        with left:
            st.markdown(f"**Файл:** {selected.filename}")
            st.markdown(f"**Статус:** `{selected.status}`")
            if selected.error:
                st.error(selected.error)

            if selected.status != "completed":
                st.info("Результат появится после завершения обработки.")
            else:
                st.markdown("**Ответ модели:**")
                # Используем чистый Markdown для правильного рендеринга заголовков и форматирования
                # Streamlit автоматически добавит прокрутку для длинного контента
                st.markdown(selected.result or "")

        with right:
            st.markdown("### Решение эксперта")
            existing = st.session_state.decisions.get(selected_id, {})
            decision = st.radio(
                "Итог",
                options=["поддержать", "отклонить", "на доработку"],
                index=["поддержать", "отклонить", "на доработку"].index(existing.get("decision", "на доработку")),
            )
            comment = st.text_area("Комментарий эксперта", value=existing.get("comment", ""), height=220)

            if st.button("💾 Сохранить решение"):
                st.session_state.decisions[selected_id] = {"decision": decision, "comment": comment}
                st.success("Сохранено.")
