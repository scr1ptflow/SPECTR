import atexit
from concurrent.futures import ThreadPoolExecutor

_api_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="api")


def submit(fn, *args, **kwargs):
    return _api_executor.submit(fn, *args, **kwargs)


@atexit.register
def _shutdown():
    _api_executor.shutdown(wait=False)
