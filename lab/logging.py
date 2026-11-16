import logging
import re
import traceback


class RedactResultURLs(logging.Filter):
    def filter(self, record):
        def redact(value):
            return re.sub(r'(/(?:result|image|delete)/)[A-Za-z0-9_-]+', r'\1[private]', value)
        record.msg = redact(record.getMessage())
        record.args = ()
        if record.exc_info:
            record.exc_text = redact(''.join(traceback.format_exception(*record.exc_info)))
            record.exc_info = None
        return True
