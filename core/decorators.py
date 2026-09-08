import inspect
import time
import traceback
from functools import wraps

from core.logging import get_logger


SENSITIVE_FIELDS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "secret",
}


def sanitize(value):
    """
    Удаляет потенциально чувствительные данные
    перед записью в лог.
    """

    if isinstance(value, dict):
        return {
            key: "***"
            if key.lower() in SENSITIVE_FIELDS
            else sanitize(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            sanitize(item)
            for item in value
        ]

    if isinstance(value, (str, int, float, bool, type(None))):
        return value

    return f"<{type(value).__name__}>"


def log_execution(
    event: str,
    operation: str | None = None,
):
    """
    Логирует выполнение sync/async функции.

    При ошибке дополнительно записывает в extra:

        file      — файл, где реально произошла ошибка
        line      — строка, где реально произошла ошибка
        function  — функция, где реально произошла ошибка
        error     — тип и сообщение ошибки

    Эти поля используются FixOps.
    """

    def decorator(func):

        operation_name = operation or func.__name__

        # ====================================================
        # ASYNC
        # ====================================================

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):

                start = time.perf_counter()

                log = get_logger(
                    event=event,
                    operation=operation_name,
                    function=func.__qualname__,
                    module=func.__module__,
                )

                log.debug("Function started")

                try:

                    result = await func(
                        *args,
                        **kwargs,
                    )

                    duration_ms = (
                        time.perf_counter() - start
                    ) * 1000

                    log.bind(
                        status="success",
                        severity="INFO",
                        duration_ms=round(
                            duration_ms,
                            2,
                        ),
                    ).info(
                        "Function completed"
                    )

                    return result

                except Exception as exc:

                    duration_ms = (
                        time.perf_counter() - start
                    ) * 1000

                    # ============================================
                    # НАСТОЯЩЕЕ МЕСТО ОШИБКИ
                    # ============================================
                    #
                    # traceback содержит всю цепочку вызовов.
                    #
                    # Нам нужен последний кадр:
                    #
                    # main.py:63 -> action
                    #
                    # а не:
                    #
                    # core/decorators.py:... -> sync_wrapper
                    #
                    tb = traceback.extract_tb(
                        exc.__traceback__
                    )

                    last = tb[-1]

                    # ============================================
                    # ЛОГ ОШИБКИ
                    # ============================================

                    log.bind(
                        status="error",
                        severity="ERROR",
                        duration_ms=round(
                            duration_ms,
                            2,
                        ),

                        # Реальный файл ошибки.
                        file=last.filename,

                        # Реальная строка ошибки.
                        line=last.lineno,

                        # Реальная функция ошибки.
                        function=last.name,

                        # Информация об exception.
                        error={
                            "type": type(exc).__name__,
                            "message": str(exc),
                        },

                        arguments={
                            "args": sanitize(args),
                            "kwargs": sanitize(kwargs),
                        },
                    ).exception(
                        "Function failed"
                    )

                    # Передаём ошибку дальше.
                    raise

            return async_wrapper

        # ====================================================
        # SYNC
        # ====================================================

        @wraps(func)
        def sync_wrapper(*args, **kwargs):

            start = time.perf_counter()

            log = get_logger(
                event=event,
                operation=operation_name,
                function=func.__qualname__,
                module=func.__module__,
            )

            log.debug("Function started")

            try:

                result = func(
                    *args,
                    **kwargs,
                )

                duration_ms = (
                    time.perf_counter() - start
                ) * 1000

                log.bind(
                    status="success",
                    severity="INFO",
                    duration_ms=round(
                        duration_ms,
                        2,
                    ),
                ).info(
                    "Function completed"
                )

                return result

            except Exception as exc:

                duration_ms = (
                    time.perf_counter() - start
                ) * 1000

                # ================================================
                # НАСТОЯЩЕЕ МЕСТО ОШИБКИ
                # ================================================
                #
                # Например, если ошибка:
                #
                # main.py:63
                # result = data["total"] + 1
                #
                # last будет содержать:
                #
                # filename = ".../main.py"
                # lineno   = 63
                # name     = "action"
                #
                tb = traceback.extract_tb(
                    exc.__traceback__
                )

                last = tb[-1]

                # ================================================
                # ЛОГ ОШИБКИ
                # ================================================

                log.bind(
                    status="error",
                    severity="ERROR",
                    duration_ms=round(
                        duration_ms,
                        2,
                    ),

                    # Реальный файл, где произошла ошибка.
                    file=last.filename,

                    # Реальная строка ошибки.
                    line=last.lineno,

                    # Реальная функция ошибки.
                    function=last.name,

                    # Тип и сообщение ошибки.
                    error={
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },

                    # Аргументы функции.
                    arguments={
                        "args": sanitize(args),
                        "kwargs": sanitize(kwargs),
                    },
                ).exception(
                    "Function failed"
                )

                # Не поглощаем исключение.
                raise

        return sync_wrapper

    return decorator
