# `pywise`
[![PyPI version](https://badge.fury.io/py/pywise.svg)](https://badge.fury.io/py/pywise) [![CircleCI](https://circleci.com/gh/malcolmgreaves/pywise/tree/main.svg?style=svg)](https://circleci.com/gh/malcolmgreaves/pywise/tree/main) [![Coverage Status](https://coveralls.io/repos/github/malcolmgreaves/pywise/badge.svg?branch=main)](https://coveralls.io/github/malcolmgreaves/pywise?branch=main)

Contains functions that provide general utility and build upon the Python 3 standard library. It has no external dependencies.
  - `serialization`: serialization & deserialization for `NamedTuple`-deriving & `@dataclass` decorated classes
  - `archives`: uncompress tar archives
  - `common`: utilities
  - `schema`: obtain a `dict`-like structure describing the fields & types for any serialzable type (helpful to view as JSON)

This project's most notable functionality are the `serialize` and `deserialize` funtions of `core_utils.serialization`.
Take a look at the end of this document for example use.



## Development Setup
This project uses [`poetry`](https://python-poetry.org/) for virtualenv and dependency management. We recommend using [`brew`](https://brew.sh/) to install `poetry` system-wide.

To install the project's dependencies, perform:
```
poetry install
```

Every command must be run within the `poetry`-managed environment.
For instance, to open a Python shell, you would execute:
```
poetry run python
```
Alternatively, you may activate the environment by performing `poetry shell` and directly invoke Python programs.

### Development Practices
Install pre-commit `git` hooks using `pre-commit install`. Hooks are defined in the `.pre-commit-config.yaml` file.

CI enforces linting using all pre-commit hooks.

NOTE: Dependencies in hooks **MUST** be kept in-sync with the 
      `dev-dependencies` section in `pyproject.toml` for `poetry.


#### Testing
To run tests, execute:
```
poetry run pytest -v
```
To run tests against all supported environments, use [`tox`](https://tox.readthedocs.io/en/latest/):
```
poetry run tox -p
```
NOTE: To run `tox`, you must have all necessary Python interpreters available.
      We recommend using [`pyenv`](https://github.com/pyenv/pyenv) to manage your Python versions.


#### Dev Tools
This project uses `ruff` for code formatting and  linting. Static type checking is enforced using `mypy`.
Use the following commands to ensure code quality:
```
# code format and lint: applies fixes automatically in-place if possible
ruff format .
ruff check --fix .

# typechecks
mypy --ignore-missing-imports --follow-imports=silent --show-column-numbers --warn-unreachable --install-types --non-interactive --check-untyped-defs .
```


## Documentation via Examples

#### Nested @dataclass and NamedTuple
Lets say you have an address book that you want to write to and from JSON.
We'll define our data types for our `AddressBook`:

```python
from typing import Optional, Union, Sequence
from dataclasses import dataclass
from enum import Enum, auto

@dataclass(frozen=True)
class Name:
    first: str
    last: str
    middle: Optional[str] = None

class PhoneNumber(NamedTuple):
    area_code: int
    number: int
    extension: Optional[int] = None

@dataclass(frozen=True)
class EmailAddress:
    name: str
    domain: str

class ContactType(Enum):
    personal, professional = auto(), auto()

class Emergency(NamedTuple):
    full_name: str
    contact: Union[PhoneNumber, EmailAddress]

@dataclass(frozen=True)
class Entry:
    name: Name
    number: PhoneNumber
    email: EmailAddress
    contact_type: ContactType
    emergency_contact: Emergency

@dataclass(frozen=True)
class AddressBook:
    entries: Sequence[Entry]
```

For illustration, let's consider the following instantiated `AddressBook`:
```python
ab = AddressBook([
    Entry(Name('Malcolm', 'Greaves', middle='W'), 
          PhoneNumber(510,3452113),
          EmailAddress('malcolm','world.com'),
          contact_type=ContactType.professional,
          emergency_contact=Emergency("Superman", PhoneNumber(262,1249865,extension=1))
    ),
])
```

We can convert our `AddressBook` data type into a JSON-formatted string using `serialize`:
```python
from core_utils.serialization import serialize
import json

s = serialize(ab)
j = json.dumps(s, indent=2)
print(j)
```

And we can easily convert the JSON string back into a new instanitated `AddressBook` using `deserialize`:
```python
from core_utils.serialization import deserialize

d = json.loads(j)
new_ab = deserialize(AddressBook, d)
print(ab == new_ab)
# NOTE: The @dataclass(frozen=True) is only needed to make this equality work.
#       Any @dataclass decorated type is serializable. 
```

Note that the `deserialize` function needs the type to deserialize the data into. The deserizliation
type-matching is _structural_: it will work so long as the data type's structure (of field names and
associated types) is compatible with the supplied data.


#### Custom Serialization
In the event that one desires to use `serialize` and `deserialize` with data types from third-party libraries (e.g. `numpy` arrays) or custom-defined `class`es that are not decorated with `@dataclass` or derive from `NamedTuple`, one may supply a `CustomFormat`.

`CustomFormat` is a mapping that associates precise types with custom serialization functions. When supplied to `serialize`, the values in the mapping accept an instance of the exact type and produces a serializable representation. In the `deserialize` function, they convert such a serialized representation into a bonafide instance of the type.

To illustrate their use, we'll deine `CustomFormat` `dict`s that allow us to serialize `numpy` multi-dimensional arrays:
```python
import numpy as np
from core_utils.serialization import *


custom_serialization: CustomFormat = {
    np.ndarray: lambda arr: arr.tolist()
}

custom_deserialization: CustomFormat = {
    np.ndarray: lambda lst: np.array(lst)
}
```

Now, we may supply `custom_{serialization,deserialization}` to our functions. We'll use them to perform a "round-trip" serialization of a four-dimensional array of floating point numbers to and from a JSON-formatted `str`:
```python
import json

v_original = np.random.random((1,2,3,4))
s = serialize(v_original, custom=custom_serialization)
j = json.dumps(s)

d = json.loads(j)
v_deser = deserialize(np.ndarray, d, custom=custom_deserialization)

print((v_original == v_deser).all())
```

It's important to note that, when supplying a `CustomFormat` the serialization functions take priority over the default behavior (except for `Any`, as it is _always_ considered a pass-through). Moreover, types must match **exactly** to the keys in the mapping. Thus, if using a generic type, you must supply separate key-value entires for each distinct type parameterization.

