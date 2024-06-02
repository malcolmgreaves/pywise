from typing import Protocol, Sequence

__all__: Sequence[str] = (
    "WritableFile",
    "Writable",
)


class Writable(Protocol):
    """Supports writing strings and flushing."""

    def flush(self) -> None:
        """Force any internally buffered contents to be written to the underlying store."""
        ...  # pragma: no cover

    def write(self, s: str) -> int:
        """Write the string. Return the number of bytes written."""
        ...  # pragma: no cover


class WritableFile(Writable, Protocol):
    """Something writable that has a filename."""

    @property
    def name(self) -> str:
        """The name of the file being written."""
        ...  # pragma: no cover
