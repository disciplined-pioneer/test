"""
core/logging.py — настройка логирования примера проекта через loguru.

Адаптировано под структуру проекта FixOps Code Intelligence:

  - пакет лежит в core/logging.py;
  - файловый лог пишется в единую директорию логов проекта
    (по умолчанию <корень проекта>/logs/app.log);
  - окружение (production/development) переопределяется переменной
    окружения APP_ENV, по умолчанию — production (JSON в stdout,
    как и было в исходном core).

Сразу после импорта модуля создаётся директория логов и регистрируются
два sink-а (консоль и файл). Готовый к использованию логгер — `app_logger`,
а фабрика `get_logger(event, **context)` добавляет к событию уникальный
event_id и произвольный контекст.
"""

import os
import sys
import uuid
from pathlib import Path

from loguru import logger


# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

# Проект: core/logging.py -> корень проекта
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVICE_NAME = os.environ.get("APP_SERVICE_NAME", "app-service")
ENV = os.environ.get("APP_ENV", "production")

# Директория логов: можно переопределить переменной окружения LOG_DIR,
# по умолчанию — <корень проекта>/logs (там же лежат остальные артефакты пайплайна).
LOGS_DIR = Path(os.environ.get("LOG_DIR", str(PROJECT_ROOT / "logs")))
os.makedirs(LOGS_DIR, exist_ok=True)

logger.remove()


# ============================================================
# CONSOLE
# ============================================================

if ENV == "production":

    # Production:
    # JSON -> stdout -> Docker / Kubernetes / FixOps
    logger.add(
        sys.stdout,
        serialize=True,
        level="INFO",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

else:

    # Development:
    # Красивый лог для человека
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<magenta>{extra[event]: <22}</magenta> | "
            "<cyan>{name}:{function}:{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
        level="DEBUG",
        backtrace=True,
        diagnose=True,
    )


# ============================================================
# FILE
# ============================================================

logger.add(
    str(LOGS_DIR / "app.log"),
    serialize=True,
    rotation="10 MB",
    retention="7 days",
    compression="gz",
    enqueue=True,
    level="INFO",
    backtrace=True,
    diagnose=False,
)


# ============================================================
# BASE LOGGER
# ============================================================

app_logger = logger.bind(
    service=SERVICE_NAME,
    environment=ENV,
)


def get_logger(
    event: str,
    **context,
):
    """
    Создаёт logger с контекстом события.
    """

    return app_logger.bind(
        event=event,
        event_id=str(uuid.uuid4()),
        **context,
    )