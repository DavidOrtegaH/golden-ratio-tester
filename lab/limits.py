"""Single-process, time-bounded abuse protection; never trusts proxy headers."""
from collections import OrderedDict
import hashlib
import secrets
import threading
import time


class AnalysisLimiter:
    def __init__(self, window=60, capacity=512):
        self.window, self.capacity = window, capacity
        self.entries = OrderedDict()
        self.lock = threading.Lock()
        self.salt = secrets.token_bytes(32)
        self.timer = None

    def _purge(self, now):
        while self.entries and next(iter(self.entries.values()))[0] <= now:
            self.entries.popitem(last=False)

    def _schedule(self):
        if self.timer is None and self.entries:
            delay = max(.001, next(iter(self.entries.values()))[0] - time.monotonic())
            self.timer = threading.Timer(delay, self._expire)
            self.timer.daemon = True
            self.timer.start()

    def _expire(self):
        with self.lock:
            self.timer = None
            self._purge(time.monotonic())
            self._schedule()

    def allow(self, address, limit):
        key = hashlib.blake2s(address.encode(), key=self.salt, digest_size=16).digest()
        now = time.monotonic()
        with self.lock:
            self._purge(now)
            if key not in self.entries:
                if len(self.entries) >= self.capacity:
                    self.entries.popitem(last=False)
                self.entries[key] = [now + self.window, 0]
            item = self.entries[key]
            self._schedule()
            if item[1] >= limit:
                return False
            item[1] += 1
            return True

    def clear(self):
        with self.lock:
            self.entries.clear()
            if self.timer:
                self.timer.cancel()
                self.timer = None


limiter = AnalysisLimiter()
