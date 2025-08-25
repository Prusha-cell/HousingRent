import logging
from contextvars import ContextVar

request_id_ctx = ContextVar("request_id", default="-")
user_id_ctx = ContextVar("user_id", default="-")


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get("-")
        record.user_id = user_id_ctx.get("-")
        return True
