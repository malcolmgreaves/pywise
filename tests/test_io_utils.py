import tempfile

from core_utils.io_utils import Writable, WritableFile


def test_named_tempfi_is_writable_file():
    with tempfile.NamedTemporaryFile(mode="wt") as f:
        _write_named(f, "hello world!")
        with open(f.name, "rt") as rt:
            content = rt.read()
        assert content == "hello world!"


def _write_named(f: WritableFile, content: str) -> None:
    assert len(f.name) > 0
    _write(f, content)


def _write(f: Writable, content: str) -> None:
    f.write(content)
    f.flush()
