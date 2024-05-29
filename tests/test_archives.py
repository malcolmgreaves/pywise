import os
import shutil
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple

from pytest import mark, raises

from core_utils.archives import CompressionTypes, extract_archive


def test_extract_archive_fail_conditions():
    with raises(IOError):
        # source is not a file
        extract_archive(Path("."), Path("."))

    with raises(ValueError):
        # destination is not empty
        extract_archive(Path(__file__), Path(__file__).parent, overwrite=False)

    with raises(ValueError):
        # source archive has unknown filename and extension is not explicit
        with TemporaryDirectory() as tempdir:
            _, archive_file = _create_archive(tempdir, "dir_for_fail", "gz")
            without_extension = str(archive_file).removesuffix(".gz")
            shutil.move(str(archive_file), without_extension)

            extract_archive(Path(without_extension), Path("unreachable"), compression_ext=None)


@mark.parametrize("ext", ["gz", "bz2", "xz"])
def test_extract_archive(ext: CompressionTypes):
    _extract_archive_test_helper("dir_to_archive", ext)


def _extract_archive_test_helper(dirname: str, extension: CompressionTypes) -> None:
    with TemporaryDirectory() as tempdir:
        tar_contents, archive_file = _create_archive(tempdir, dirname, extension)

        # remove our extracted dir so we can be sure we are creating it fresh each time in the tests below
        shutil.rmtree(tar_contents)

        with TemporaryDirectory() as d:
            dest = Path(d) / "destination"
            extract_archive(archive_file, dest)
            assert dest.is_dir()
            contents = list(os.listdir(str(dest.absolute())))
            assert len(contents) > 0

            extract_archive(archive_file, dest, overwrite=True)
            assert dest.is_dir()
            contents = list(os.listdir(str(dest.absolute())))
            assert len(contents) > 0

        with TemporaryDirectory() as d:
            dest = Path(d) / "destination"
            extract_archive(archive_file, dest, compression_ext=extension)
            assert dest.is_dir()
            contents = list(os.listdir(str(dest.absolute())))
            assert len(contents) > 0


def _create_archive(tempdir: str, dirname: str, extension: CompressionTypes) -> Tuple[Path, Path]:
    # make a directory
    tar_contents = Path(tempdir) / dirname
    tar_contents.mkdir()
    # put some files in it
    for i in range(5):
        file = Path(tempdir) / f"file_{i}"
        with open(file, "wt") as w:
            w.write("hello world\n")
            w.write(f"this is file {i}\n")
    # create the .tar.{extension} archive
    archive_file = Path(tempdir) / f"archive.tar.{extension}"
    with tarfile.open(archive_file, f"w:{extension}") as w:
        w.add(tar_contents, arcname=dirname)
    # give the caller the original & compressed archive files
    return tar_contents, archive_file
