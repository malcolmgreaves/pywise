from typing import (
    Type,
    Iterable,
    Union,
    Any,
    Mapping,
    Sequence,
    get_args,
    cast,
    Callable,
    Tuple,
)
from dataclasses import is_dataclass

from core_utils.common import type_name, checkable_type
from core_utils.serialization import (
    is_typed_namedtuple,
    _namedtuple_field_types,
    _dataclass_field_types_defaults,
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
            f"Failed to discover field-type attributes of type: '{nt_or_dc_type}",
            e,
        )


def _dict_type(t: type):
    if is_typed_namedtuple(t) or is_dataclass(t):
        if is_typed_namedtuple(t):
            field_types_of: Callable[
                [], Iterable[Tuple[str, type]]
            ] = lambda: _namedtuple_field_types(
                t  # type: ignore
            )
        else:

            def field_types_of() -> Iterable[Tuple[str, type]]:
                for a, b, _ in _dataclass_field_types_defaults(t):
                    yield a, b

        accum = {name: _dict_type(field_type) for name, field_type in field_types_of()}
        return accum

    else:
        tn = type_name(t)
        if "typing.Union" not in tn and "typing.Optional" not in tn:
            checkable_t: Type = checkable_type(t)
            if issubclass(checkable_t, Mapping):
                try:
                    _args = get_args(t)
                    key_t: type = cast(type, _args[0])
                    val_t: type = cast(type, _args[1])
                except Exception as e:
                    raise TypeError(
                        f"Could not extract key & value types from dict type: '{t}'"
                    ) from e
                else:
                    k = _dict_type(key_t)
                    v = _dict_type(val_t)
                    return {k: v}

            elif issubclass(checkable_t, Iterable) and t != str:
                try:
                    inner_t: type = cast(type, get_args(t)[0])
                except Exception as e:
                    raise TypeError(
                        f"Could not extract inner type from iterable type: '{t}'"
                    ) from e
                else:
                    return [_dict_type(inner_t)]
        return tn
