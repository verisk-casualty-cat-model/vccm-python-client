import inspect
import json
import traceback

from config.get_logger import get_logger

logger = get_logger(__name__)


class AriumAPACResponseException(Exception):
    def __init__(self, response):
        self.response = response


class EventImportException(Exception):
    """Bulk event import / export request rejected by the server, e.g. CSV rows failing validation."""

    def __init__(self, status_code: int, message: str, errors: list | None = None):
        self.status_code = status_code
        self.errors = errors or []
        details = "".join(f"\n\t{error}" for error in self.errors)
        super().__init__(f"{status_code} - {message}{details}")

    @classmethod
    def from_response(cls, response) -> "EventImportException":
        # Error body is {"message": ..., "details": {"errors": [...]}}; S3 answers with XML instead
        try:
            content = json.loads(response.content)
            message = content.get("message") or response.reason
            errors = (content.get("details") or {}).get("errors", [])
        except (ValueError, AttributeError):
            message = response.text or response.reason
            errors = []
        return cls(response.status_code, message, errors)


class AriumAPACException(Exception):
    def __init__(self, exception, message, **kwargs):
        if isinstance(exception, AriumAPACException):
            self.message = "\n\t" + message.format(**kwargs) + exception.message
        else:
            logger.error(exception)
            logger.error(traceback.format_exc())
            self.message = (
                "\n\t"
                + message.format(**kwargs)
                + f"\n\t{exception.__class__.__name__}: {str(exception)}"
            )

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message


def handle_exception(e):
    status_code = e.response.status_code
    reason = e.response.reason if e.response.reason else "unknown"

    try:
        content = json.loads(e.response.content)
        content_message = content.get(
            "message", content.get("error", content.get("errors", content))
        )
        content_details = content.get("details", None)
    except json.decoder.JSONDecodeError:
        content_message = e.response.content
        content_details = None

    message = f"Exception occurred: {reason} - {status_code} - {content_message}"

    if content_details:
        message += f" - {content_details}"

    logger.exception(message)


def exception_handler(fun):
    def wrapper(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except AriumAPACResponseException as e:
            handle_exception(e)
            raise Exception from None
        except Exception as e:
            logger.exception(f"Exception occurred: {e}")
            raise Exception from None

    return wrapper


class ExceptionHandlerDecorator:
    def __init__(self, message):
        self.message = message

    def __call__(self, fun):
        def decorator(*args, **kwargs):
            args_with_names = {
                **dict(zip(fun.__code__.co_varnames[: fun.__code__.co_argcount], args))
            }
            default_args_with_names = {
                k: v.default
                for k, v in inspect.signature(fun).parameters.items()
                if v.default is not inspect.Parameter.empty
            }
            all_args = {**default_args_with_names, **args_with_names}
            all_args.update(kwargs)

            try:
                return fun(**all_args)
            except Exception as e:
                raise AriumAPACException(e, self.message, **all_args).with_traceback(
                    None
                ) from None

        return decorator
