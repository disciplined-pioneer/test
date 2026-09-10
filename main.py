"""
Тестовый проект на FastAPI.

В проект НАМЕРЕННО внесена ошибка (см. пометку "BUG" ниже).
Цель проекта — служить тестовым стендом: нажатие кнопки на странице
вызывает серверный эндпоинт, который падает с ошибкой. Отдельно
поставляется файл patch.diff, который эту ошибку исправляет.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Импорты инфраструктуры логирования согласно документации
from core.decorators import log_execution
from core.logging import get_logger
from core.middleware import request_id_middleware

app = FastAPI(title="Bug Test Project")

# Подключение middleware для генерации request_id на каждый HTTP-запрос
app.middleware("http")(request_id_middleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Простое "хранилище" состояния в памяти процесса.
data = {
    "count": 0,
}


@app.get("/")
@log_execution(event="index.render")
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Мой сайт"} # контекст для шаблона (опционально)
    )


@app.post("/api/action")
@log_execution(event="action.execute")
def action():
    """
    Эндпоинт, вызываемый нажатием кнопки на странице.
    """
    log = get_logger(event="action.execute", current_count=data["count"])
    log.info("Processing action request")

    data["count"] += 1
    result = data["total"] + 1

    return JSONResponse({"count": data["count"], "result": result})


@app.get("/api/status")
@log_execution(event="status.check")
def status():
    """Вспомогательный эндпоинт для проверки состояния сервера."""
    log = get_logger(event="status.check")
    log.debug("Status requested", current_data=data)
    return {"status": "ok", "data": data}
