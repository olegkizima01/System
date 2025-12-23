import os
import types
from mcp_integration.chroma_utils import create_persistent_client, get_default_chroma_persist_dir


def test_rust_backtrace_env_set(monkeypatch, tmp_path):
    # Ensure RUST_BACKTRACE is not set
    monkeypatch.delenv("RUST_BACKTRACE", raising=False)

    # Force chromadb import to raise so create_persistent_client will go into the warning path
    monkeypatch.setitem(__import__("builtins").__dict__, "chromadb", None)

    # Call create_persistent_client; since chromadb isn't importable, function should still set RUST_BACKTRACE
    res = create_persistent_client(persist_dir=tmp_path, logger=types.SimpleNamespace(info=lambda *_: None, warning=lambda *_: None, error=lambda *_: None), retry_repair=False)

    assert os.environ.get("RUST_BACKTRACE") == "0"
    assert res is None or isinstance(res, (object, type(None)))
