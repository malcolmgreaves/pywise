import json
from dataclasses import dataclass
from enum import Enum, auto
from typing import NamedTuple, Optional, Sequence, Union

from pytest import fixture

from core_utils.serialization import deserialize, serialize


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


@fixture(scope="module")
def ab():
    return AddressBook(
        [
            Entry(
                Name("Malcolm", "Greaves", middle="W"),
                PhoneNumber(510, 3452113),
                EmailAddress("malcolm", "world.com"),
                contact_type=ContactType.professional,
                emergency_contact=Emergency("Superman", PhoneNumber(262, 1249865, extension=1)),
            ),
        ]
    )


def test_readme_example(ab):
    s = serialize(ab)
    j = json.dumps(s, indent=2)
    d = json.loads(j)
    new_ab = deserialize(AddressBook, d)
    assert new_ab == ab, "De-serialized is the same as original."
