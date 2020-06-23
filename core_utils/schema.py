from typing import Type, Iterable, Union, Any, Mapping, Sequence
from dataclasses import is_dataclass

from core_utils.common import type_name, checkable_type
from core_utils.serialization import (
    is_typed_namedtuple,
    _namedtuple_field_types,
    _dataclass_field_types,
)


__all__ = ["dict_type_representation", "Discover"]

Discover = Union[Mapping[str, Union[str, Mapping[str, Any]]], Sequence[Any]]
"""Schematic representation of a :func:`serializable` datatype.

A dictionary of (field name, discovery type on field) pairs or a sequence thereof.
This recursive data type definition can't be expressed in mypy yet (0.720).
A complete, accurate recursive type definition is:
```
Discover = Union[Mapping[str, Union[type, Discover]], Sequence[Discover]]
```
"""


def dict_type_representation(nt_or_dc_type: Type) -> Discover:
    """The dictionary JSON-like named attribute & expected type representation computed
    from the supplied NamedTuple-deriving or @dataclass decorated type.
    """
    try:
        return _dict_type(nt_or_dc_type)
    except Exception as e:
        raise TypeError(
            f"Failed to discover field-type attributes of type: '{nt_or_dc_type}", e,
        )


def _dict_type(t: type):
    if is_typed_namedtuple(t) or is_dataclass(t):
        field_types_of = (
            _namedtuple_field_types
            if is_typed_namedtuple(t)
            else _dataclass_field_types
        )
        accum = {name: _dict_type(field_type) for name, field_type in field_types_of(t)}
        return accum

    else:
        tn = type_name(t)
        if "typing.Union" not in tn and "typing.Optional" not in tn:
            checkable_t: Type = checkable_type(t)
            if issubclass(checkable_t, Mapping):
                try:
                    key_t: type = t.__args__[0]  # type: ignore
                    val_t: type = t.__args__[1]  # type: ignore
                except Exception as e:
                    raise TypeError(
                        f"Could not extract key & value types from dict type: '{t}'"
                    ) from e
                k = _dict_type(key_t)
                v = _dict_type(val_t)
                return {k: v}

            elif issubclass(checkable_t, Iterable) and t != str:
                try:
                    inner_t: type = t.__args__[0]  # type: ignore
                except Exception as e:
                    raise TypeError(
                        f"Could not extract inner type from iterable type: '{t}'"
                    ) from e
                return [_dict_type(inner_t)]
        return tn
