import time
import threading
from pathlib import Path
import shutil
from datetime import datetime, timezone, timedelta

from src.config.settings import settings, UPLOAD_DIR


class SessionCleaner:
    def __init__(self, ttl_hours: int | None = None):
        self.ttl_hours = ttl_hours or settings.SESSION_TTL_HOURS
        self.upload_dir = Path(UPLOAD_DIR)
        self._timer: threading.Timer | None = None

    def clean_expired(self) -> int:
        expired_count = 0
        if not self.upload_dir.exists():
            return 0

        cutoff = time.time() - (self.ttl_hours * 3600)
        for session_dir in self.upload_dir.iterdir():
            if not session_dir.is_dir():
                continue
            try:
                mtime = session_dir.stat().st_mtime
                if mtime < cutoff:
                    shutil.rmtree(session_dir, ignore_errors=True)
                    expired_count += 1
            except Exception:
                continue

        return expired_count

    def start_periodic(self, interval_minutes: int = 60):
        self._run_and_reschedule(interval_minutes)

    def _run_and_reschedule(self, interval_minutes: int):
        try:
            self.clean_expired()
        except Exception:
            pass
        self._timer = threading.Timer(interval_minutes * 60, self._run_and_reschedule, [interval_minutes])
        self._timer.daemon = True
        self._timer.start()

    def stop(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None
