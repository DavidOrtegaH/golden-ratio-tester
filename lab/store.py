"""Single-process bounded storage with active expiry; never writes images to disk."""
import secrets
import threading
import time
from collections import OrderedDict


class ResultStore:
    def __init__(self, ttl=900, max_bytes=192 * 1024 * 1024):
        self.ttl, self.max_bytes = ttl, max_bytes
        self.items = OrderedDict()
        self.timers = {}
        self.lock = threading.RLock()
        self.used = 0

    def delete(self, token):
        with self.lock:
            item = self.items.pop(token, None)
            if item:
                self.used -= item[2]
            timer = self.timers.pop(token, None)
            if timer:
                timer.cancel()

    def purge(self):
        with self.lock:
            for key, (expiry, _, _) in list(self.items.items()):
                if expiry <= time.monotonic():
                    self.delete(key)

    def put(self, value):
        size = len(value['original']) + len(value['overlay'])
        if size > self.max_bytes:
            raise ValueError('size')
        with self.lock:
            self.purge()
            while self.items and (self.used + size > self.max_bytes or len(self.items) >= 32):
                self.delete(next(iter(self.items)))
            token = secrets.token_urlsafe(32)
            self.items[token] = (time.monotonic() + self.ttl, value, size)
            self.used += size
            # Also actively erase idle results, even if no subsequent request arrives.
            timer = threading.Timer(self.ttl, self.delete, args=(token,))
            timer.daemon = True
            self.timers[token] = timer
            timer.start()
            return token

    def get(self, token):
        with self.lock:
            self.purge()
            item = self.items.get(token)
            return item[1] if item else None


store = ResultStore()
