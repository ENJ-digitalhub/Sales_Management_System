from contextlib import contextmanager

@contextmanager
def get_session():
    # Temporary mock context manager
    class MockSession:
        def query(self, model): return self
        def filter(self, *args, **kwargs): return self
        def first(self): return None
    yield MockSession()