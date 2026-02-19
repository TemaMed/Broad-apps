import time

class CircuitBreaker:
    def __init__(self, fail_threshold: int = 5, reset_after_s: int = 60):
        self.fail_threshold = fail_threshold
        self.reset_after_s = reset_after_s
        self.fail_count = 0
        self.opened_at = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.time() - self.opened_at >= self.reset_after_s:
            self.opened_at = None
            self.fail_count = 0
            return True
        return False

    def on_success(self) -> None:
        self.fail_count = 0
        self.opened_at = None

    def on_failure(self) -> None:
        self.fail_count += 1
        if self.fail_count >= self.fail_threshold:
            self.opened_at = time.time()
