# `core_utils`

Contains functions that provide general utility and build upon the Python 3 standard library. It has no external dependencies.
  - `serialization`: serialization & deserialization for `NamedTuple`-deriving & `@dataclass` decorated classes
  - `archives`: uncompress tar archives
  - `common`: utilities
  - `schema`: obtain a `dict`-like structure describing the fields & types for any serialzable type (helpful to view as JSON)

This project's most notable functionality are the `serialize` and `deserialize` funtions of `core_utils.serialization`.
Take a look at the end of this document for example use.



## Development Setup
Create a distinct environment for this code using coda via:
```
conda env create -y -n pycore -python=3.8
```
And activate it via:
```
conda activate pycore
```
And make the project's code available in the environment:
```
pip install -e .
```


## Testing
Install test and dev tool dependencies via:
```
pip install -r requirements-test.txt
```
Or with `pip install -e .[test]`.

Run all tests via:
```
pytest
```

Additionally, we use `tox` to perform tests across Python 3.8+ as well as 3.7+. To run both tests in parallel, do:
```
tox -p
```


## Dev Tools
This project uses `black` for code formatting, `flake8` for linting, and
`mypy` for type checking. Use the following commands to ensure code quality:
```
# formats all code in-place
black .

# typechecks
mypy --ignore-missing-imports --follow-imports=silent --show-column-numbers --warn-unreachable .

# lints code
flake8 --max-line-length=100 --ignore=E501,W293,E303,W291,W503,E203,E731,E231 .
```


## Examples

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
'''

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

NOTE: The `deserialize` function needs the type to deserialize the data into.

