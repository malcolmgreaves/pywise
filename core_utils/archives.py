import shutil
import tarfile
from pathlib import Path
from typing import Literal, Optional, Sequence

__all__: Sequence[str] = (
    "extract_archive",
    "CompressionTypes",
)

CompressionTypes = Literal["gz", "bz2", "xz"]


def extract_archive(
    src_archive: Path,
    dest_dir: Path,
    compression_ext: Optional[CompressionTypes] = None,
    overwrite: bool = False,
) -> None:
    """Uncompress and extract the source tar archive as a directory as the named destination path.

    This function extracts the (possibly compressed) tar archive, specified by :param:`src_archive`,
    and writes its contents as a directory, specified by :param:`dest_dir`.

    The read mode is determined by the :param:`src_archive`'s filename extension. If no known compression
    extension is found ('gz', 'bz2', and 'xz'), then :func:`tarfile.open`'s "transparent read mode" is
    used.

    To override this path-dependant behavior, :param:`compression_ext` may be supplied as the exact
    read mode variant to use in the underlying :func:`tarfile.open` call. Valid compression schemes are:
      - 'gz'
      - 'bz2'
      - 'xz'
    By default, the :param:`src_archive` filename extension is inspected to determine the compression schema.

    The :param:`overwrite` parameter controls whether or not the destination directory is removed before
    extraction, if present. By default, this function will fail with a `ValueError` if the destination
    is already a file or directory.

    WARNING: SIDE EFFECT: Changes local disk contents.

    :raises IOError If source archive is not a file.
    :raises ValueError If destination is occupied and overwrite is false.
    :raises Exception On problems during tar file extraction and decompression.
    """
    if not src_archive.is_file():
        raise IOError(f"Source artifact file does not exist: {src_archive}")
    if not overwrite and dest_dir.exists():
        raise ValueError(f"Destination exists and overwrite is false: {dest_dir}")

    if compression_ext is None:
        if src_archive.name.endswith("gz"):
            comp_ext: Literal['gz', 'bz2', 'xz', '*'] = "gz"
        elif src_archive.name.endswith("bz2"):
            comp_ext = "bz2"
        elif src_archive.name.endswith("xz"):
            comp_ext = "xz"
        else:
            comp_ext = "*"
    else:
        comp_ext = compression_ext
    mode = f"r:{comp_ext}"

    with tarfile.open(name=str(src_archive.absolute()), mode=mode) as archive:
        if dest_dir.exists() and overwrite:
            shutil.rmtree(dest_dir)
        archive.extractall(path=str(dest_dir.absolute()))
