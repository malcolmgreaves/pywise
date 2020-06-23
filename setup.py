from pathlib import Path

from setuptools import find_packages, setup
from typing import Sequence, Mapping


def read_requirements(fi: str) -> Sequence[str]:
    def proc_req(r):
        r = r.strip()
        if len(r) == 0 or any(map(lambda x: r.startswith(x), ["#", ".", "-e"])):
            return None
        return r

    with open(fi, "rt") as rt:
        return list(filter(None, map(proc_req, rt.read().splitlines())))


def version() -> str:
    try:
        with open("VERSION", "rt") as rt:
            return rt.read()
    except FileNotFoundError:
        return ""


if Path("./requirements-test.txt").is_file():
    REQS: Mapping[str, Sequence[str]] = {
        "install": [],
        "test": read_requirements("requirements-test.txt"),
    }
else:
    print("WARNING: tox install? No 'requirements-test.txt' present!")
    REQS = {"install": [], "test": []}

setup(
    name="pycore",
    version=version(),
    license="Apache 2.0",
    packages=find_packages(exclude=[]),
    install_requires=REQS["install"],
    tests_require=REQS["test"],
    include_package_data=True,
    # support: pip install '.[test]', pip install '.[install]'
    extras_require=REQS,
)
