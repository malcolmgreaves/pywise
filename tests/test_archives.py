import os
import shutil
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

from pytest import raises

from core_utils.archives import extract_archive


def test_extract_archive_fail_conditions():
    with raises(IOError):
        # source is not a file
        extract_archive(Path("."), Path("."))

    with raises(ValueError):
        # destination is not empty
        print(Path(__file__) / "..")
        extract_archive(Path(__file__), Path(__file__).parent, overwrite=False)


def test_extract_archive():
    with TemporaryDirectory() as tempdir:
        # make a directory
        tar_contents = Path(tempdir) / "dir_to_archive"
        tar_contents.mkdir()
        # put some files in it
        for i in range(5):
            file = Path(tempdir) / f"file_{i}"
            with open(file, "wt") as w:
                w.write("hello world\n")
                w.write(f"this is file {i}\n")
        # create the .tar.gz archive
        archive_file = Path(tempdir) / "archive.tar.gz"
        with tarfile.open(archive_file, "w:gz") as w:
            w.add(tar_contents, arcname="dir_to_archive")
        # remove our extracted dir so we can be sure we are creating it fresh each time in
        # the tests below
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
            extract_archive(archive_file, dest, compression_ext="gz")
            assert dest.is_dir()
            contents = list(os.listdir(str(dest.absolute())))
            assert len(contents) > 0
