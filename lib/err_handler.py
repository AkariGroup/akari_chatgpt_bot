import contextlib
import os
import sys
from typing import Generator


@contextlib.contextmanager
def ignoreStderr() -> Generator[None, None, None]:
    """標準エラー出力をエラースクリーンに一時的に無視するコンテキストマネージャ。

    Returns:
        Generator[None, None, None]: コンテキストマネージャのジェネレータ。
    """
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)
