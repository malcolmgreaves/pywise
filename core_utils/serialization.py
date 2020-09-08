from enum import Enum
from typing import (  # type: ignore
    Any,
    Iterable,
    Type,
    Tuple,
    Set,
    Mapping,
    TypeVar,
    Callable,
    Optional,
    Iterator,
    Sequence,
    Union,
)
from dataclasses import dataclass, is_dataclass, Field

from core_utils.common import type_name, checkable_type

__all__ = [
    "serialize",
    "deserialize",
    "CustomFormat",
    "is_namedtuple",
    "is_typed_namedtuple",
    "MissingRequired",
    "FieldDeserializeFail",
]


SomeNamedTuple = TypeVar("SomeNamedTuple", bound=Tuple)
"""Type variable for some NamedTuple-deriving type.

NOTE: Cannot use `NamedTuple` as bound because of `mypy` bug.
      See: https://github.com/python/mypy/issues/3915
"""

CustomFormat = Mapping[Type, Callable[[Any], Any]]
"""Defines a mapping of type to function that will either serialize or deserialize that type.
See uses in :func:`serialize` and :func:`deserialize`.
"""


def serialize(
    value: Any, custom: Optional[CustomFormat] = None, no_none_values: bool = True
) -> Any:
    """Attempts to convert the `value` into an equivalent `dict` structure.

    NOTE: If the value is not a namedtuple, dataclass, mapping, enum, or iterable, then the value is
          returned as-is.

    The :param:`custom` optional mapping provides callers with the ability to handle deserialization
    of complex types that are from an external source. E.g. To serialize `numpy` arrays, one may use:
    ```
    custom = {numpy.ndarray: lambda a: a.tolist()}
    ```

    The :param:`no_none_values` flag controls whether or not this function will explicitly serialize
    fields of dataclasses and namedtuples or key-value mappings where the value is `None`. By default,
    such `None` values are ignored and their respective key-value entry will be exlcuded from returned
    serialized result. Otherwise, they are kept in the returned serialized result as `None`s.

    NOTE: If :param:`custom` is present, its serialization functions are given priority.
    NOTE: If using :param:`custom` for generic types, you *must* have unique instances for each possible
          type parametrization.
    """

    if custom is not None and type(value) in custom:
        return custom[type(value)](value)

    elif is_namedtuple(value):
        return {
            k: serialize(raw_val, custom)
            for k, raw_val in value._asdict().items()
            if (no_none_values and raw_val is not None) or (not no_none_values)
        }

    elif is_dataclass(value):
        return {
            k: serialize(v, custom)
            for k, v in value.__dict__.items()
            if (no_none_values and v is not None) or (not no_none_values)
        }

    elif isinstance(value, Mapping):
        return {
            serialize(k, custom): serialize(v, custom)
            for k, v in value.items()
            if (no_none_values and v is not None) or (not no_none_values)
        }

    elif isinstance(value, Iterable) and not isinstance(value, str):
        return list(map(lambda x: serialize(x, custom), value))

    elif isinstance(value, Enum):
        # serialize the enum value's name as it's a better identifier than the
        # actual enum value, which is usually inconsequential and arbitrary
        # additionally, the name will _always_ be a str, so we can easily
        # serialize & deserialize it
        return value.name

    else:
        return value


def deserialize(
    type_value: Type, value: Any, custom: Optional[CustomFormat] = None,
) -> Any:
    """Does final conversion of the `dict`-like `value` into an instance of `type_value`.

    NOTE: If the input type `type_value` is a sequence, then deserialization is attempted on each
    element. If it is a `dict`, then deserialization is attempted on each key and value. If this
    specified type is a namedtuple, dataclass, or enum, then it will be appropriately handled.
    Values without these explicit types are returned as-is.

    The :param:`custom` optional mapping provides callers with the ability to handle deserialization
    of complex types that are from an external source. E.g. To deserialize `numpy` arrays, one may use:
    ```
    custom = {numpy.ndarray: lambda lst: numpy.array(lst)}
    ```
    NOTE: If :param:`custom` is present, its deserialization functions are given priority.
    NOTE: If using :param:`custom` for generic types, you *must* have unique instances for each possible
          type parametrization.
    """
    if custom is not None and type_value in custom:
        return custom[type_value](value)

    if type_value == Any:
        return value

    if str(type_value).startswith("~"):
        # is a generic type alias: cannot do much with this, so return as-is
        return value

    checking_type_value: Type = checkable_type(type_value)

    if is_namedtuple(checking_type_value):
        return _namedtuple_from_dict(type_value, value, custom)

    elif is_dataclass(checking_type_value):
        return _dataclass_from_dict(type_value, value, custom)

    # NOTE: Need to have type_value instead of checking_type_value here !
    elif _is_optional(type_value):
        # obtain generic parameter \& deserialize
        if value is None:
            return None
        else:
            return deserialize(type_value.__args__[0], value, custom)

    # NOTE: Need to have type_value instead of checking_type_value here !
    elif _is_union(type_value):
        for possible_type in type_value.__args__:
            # try to deserialize the value using one of its
            # possible types
            try:
                return deserialize(possible_type, value, custom)
            except Exception:
                pass
        raise FieldDeserializeFail(
            field_name="", expected_type=type_value, actual_value=value
        )

    elif issubclass(checking_type_value, Mapping):
        k_type, v_type = type_value.__args__  # type: ignore
        return {
            deserialize(k_type, k, custom): deserialize(v_type, v, custom)
            for k, v in value.items()
        }

    elif issubclass(checking_type_value, Tuple) and checking_type_value != str:  # type: ignore
        tuple_type_args = type_value.__args__
        converted = map(
            lambda type_val_pair: deserialize(
                type_val_pair[0], type_val_pair[1], custom
            ),
            zip(tuple_type_args, value),
        )
        return tuple(converted)

    elif issubclass(checking_type_value, Iterable) and checking_type_value != str:
        (i_type,) = type_value.__args__  # type: ignore
        converted = map(lambda x: deserialize(i_type, x, custom), value)
        if issubclass(checking_type_value, Set):
            return set(converted)
        else:
            return list(converted)

    elif issubclass(checking_type_value, Enum):
        # instead of serializing the enum's _value_, we serialize it's _name_
        # so we can obtain the actual _value_ by looking in the enum type's __dict__
        # attribute with our supplied name
        return type_value[value]  # type: ignore

    else:
        # Check to see that the expected value is present & has the expected type,
        # iff the expected type is one of JSON's value types.
        if (
            (value is None and not _is_optional(checking_type_value))
            or (any(map(lambda t: t == type_value, (int, float, str, bool))))
            and not isinstance(value, checking_type_value)
        ):
            # numeric check: some ints can be a float
            if (
                float == type_value
                and isinstance(value, int)
                and int(float(value)) == value
            ):
                value = float(value)
            # and some floats can be ints
            elif int == type_value and isinstance(value, float) and int(value) == value:
                value = int(value)
            # but in general we just identified a value that
            # didn't deserialize to its expected type
            else:
                raise FieldDeserializeFail(
                    field_name="", expected_type=type_value, actual_value=value
                )

        return value


def is_namedtuple(x: Any) -> bool:
    """Check to see if a value is either an instance of or type for a namedtuple.
    https://stackoverflow.com/a/2166841
    """
    if x is None:
        return False
    if isinstance(x, type):
        t = x
    else:
        t = type(x)
    b = t.__bases__
    if len(b) != 1 or b[0] != tuple:
        return False
    if getattr(t, "_make", None) is None:
        return False
    f = getattr(t, "_fields", None)
    if not isinstance(f, tuple):
        return False
    return all(type(n) == str for n in f)


def is_typed_namedtuple(x: Any) -> bool:
    """Check to see if a value is a `typing.NamedTuple` instance or `type`.
    """
    return is_namedtuple(x) and getattr(x, "_field_types", None) is not None


def _namedtuple_from_dict(
    namedtuple_type: Type[SomeNamedTuple],
    data: dict,
    custom: Optional[CustomFormat] = None,
) -> SomeNamedTuple:
    """Initializes an instance of the given namedtuple type from a dict of its names and values.

    :param:`namedtuple_type` must be a `type` that extends `NamedTuple`. The :param:`data` `dict`
    must have the expected field names and values for the `namedtuple_type` type.
    """
    if is_namedtuple(namedtuple_type):
        try:
            field_values = tuple(
                _values_for_type(
                    _namedtuple_field_types(namedtuple_type),
                    data,
                    namedtuple_type,
                    custom,
                )
            )
            return namedtuple_type._make(field_values)  # type: ignore

        except AttributeError as ae:  # pragma: no cover
            raise TypeError(
                "Did you pass in a valid NamedTuple type? It needs ._field_types "
                "to return the list of valid field names & expected types! "
                "And ._make to accept the initialization values. Type "
                f"'{type_name(namedtuple_type)}' does not work. ",
                ae,
            )
    else:
        raise TypeError(
            f"Expecting a type derived from typing.NamedTuple or "
            f"collections.namedtuple not a: {type_name(namedtuple_type)}"
        )


def _namedtuple_field_types(
    namedtuple_type: Type[SomeNamedTuple],
) -> Iterable[Tuple[str, Type]]:
    """Obtain the fields & expected types of a NamedTuple-deriving type.
    """
    return namedtuple_type._field_types.items()  # type: ignore


def _dataclass_from_dict(
    dataclass_type: Type, data: dict, custom: Optional[CustomFormat] = None
) -> Any:
    """Constructs an @dataclass instance using :param:`data`.
    """
    is_generic_dataclass = hasattr(dataclass_type, "__origin__") and is_dataclass(
        dataclass_type.__origin__
    )
    if is_dataclass(dataclass_type) or is_generic_dataclass:
        try:
            field_and_types = list(_dataclass_field_types(dataclass_type))
            deserialized_fields = _values_for_type(
                field_and_types, data, dataclass_type, custom
            )
            deserialized_fields = list(deserialized_fields)
            field_values = dict(
                zip(map(lambda x: x[0], field_and_types), deserialized_fields)
            )
        except AttributeError as ae:
            raise TypeError(
                "Did you pass-in a type that is decorated with @dataclass? "
                "It needs a .__dataclass_fields__ member to obtain a list of field names "
                f"and their expected types. "
                f"Type '{type_name(dataclass_type)}' does not work.",
                ae,
            )
        instantiated_dataclass = dataclass_type(**field_values)
        return instantiated_dataclass
    else:
        raise TypeError(
            f"Expecting a type that is annotated with @dataclass, "
            f"not a '{type_name(dataclass_type)}'"
        )


def _dataclass_field_types(
    dataclass_type: Type, generic_to_concrete: Mapping[str, Type]
) -> Iterable[Tuple[str, Type]]:
    """Obtain the fields & their expected types for the given @dataclass type.
    """
    if hasattr(dataclass_type, "__origin__"):
        dataclass_fields = dataclass_type.__origin__.__dataclass_fields__  # type: ignore
    else:
        dataclass_fields = dataclass_type.__dataclass_fields__  # type: ignore

    def as_name_and_type(data_field: Field) -> Tuple[str, Type]:
        typ = generic_to_concrete.get(str(data_field.type), data_field.type)
        return data_field.name, typ

    return list(map(as_name_and_type, dataclass_fields.values()))


def _values_for_type(
    field_name_expected_type: Iterable[Tuple[str, Type]],
    data: dict,
    type_data: Type,
    custom: Optional[CustomFormat] = None,
) -> Iterable:
    """Constructs an instance of :param:`type_data` using the data in :param:`data`, with
    field names & expected types of :param:`field_name_expected_type` guiding construction.
    Uses :func:`deserialize`.

    :raises FieldDeserializeFail On failure to deserialize a specific field.
    :raises MissingRequired If a required field is not present.
    """
    for field_name, field_type in field_name_expected_type:  # type: ignore
        if field_name in data:
            value = data[field_name]
            # Check to see that the expected value is presnet & has the expected type,
            # iff the expected type is one of JSON's value types.
            if (
                (value is None and not _is_optional(field_type))
                or (any(map(lambda t: t == field_type, (int, float, str, bool))))
                and not isinstance(value, field_type)
            ):
                # numeric check: some ints can be a float
                if (
                    float == field_type
                    and isinstance(value, int)
                    and int(float(value)) == value
                ):
                    value = float(value)
                # and some floats can be ints
                elif (
                    int == field_type
                    and isinstance(value, float)
                    and int(value) == value
                ):
                    value = int(value)
                # but in general we just identified a value that
                # didn't deserialize to its expected type
                else:
                    raise FieldDeserializeFail(
                        field_name=field_name,
                        expected_type=field_type,
                        actual_value=value,
                    )

        elif _is_optional(field_type):  # type: ignore
            value = None
        else:
            import ipdb

            ipdb.set_trace()
            raise MissingRequired(
                field_name=field_name,
                field_expected_type=field_type,
                expected_containing_type=type_data,
            )

        try:
            if value is not None:
                yield deserialize(field_type, value, custom)  # type: ignore
            else:
                yield None
        except (FieldDeserializeFail, MissingRequired):
            raise
        except Exception as e:
            raise FieldDeserializeFail(
                field_name=field_name, expected_type=field_type, actual_value=value
            ) from e


@dataclass(frozen=True)
class MissingRequired(Exception):
    """Exception encountered when a data dict is missing a required field.
    """

    field_name: str
    field_expected_type: type
    expected_containing_type: type

    def __str__(self) -> str:
        reason = self.__cause__
        extra_reason = f" Caused by error: '{reason}'" if reason else ""
        return (
            f"Missing '{self.field_name}' (expected type of '{self.field_expected_type}') "
            f"in data dict for type '{type_name(self.expected_containing_type)}'.{extra_reason}"
        )


@dataclass(frozen=True)
class FieldDeserializeFail(Exception):
    """General exception indicating that some error occurred when deserializing a specific field.
    """

    field_name: str
    expected_type: type
    actual_value: Any

    def __str__(self) -> str:
        reason = self.__cause__
        extra_reason = f" Caused by error: '{reason}'" if reason else ""
        if len(self.field_name) > 0:
            prefix = f"Expecting field '{self.field_name}' to have"
        else:
            prefix = "Expecting to find"
        return (
            f"{prefix} type '{type_name(self.expected_type)}'. "
            f"Instead, found value '{self.actual_value}', "
            f"which has incorrect type '{type_name(type(self.actual_value))}'."
            f"{extra_reason}"
        )


def _is_optional(t: type) -> bool:
    """Evaluates to true iff the input is a type that is equivalent to an `Optional`.
    """
    try:
        type_args = t.__args__  # type: ignore
        only_one_none_type = (
            len(list(filter(lambda x: x == type(None), type_args))) == 1  # type: ignore
        )
        return only_one_none_type
    except Exception:
        return False


def _is_union(t: type) -> bool:
    """Evaluates to true iff the input is a union (not an Optional) type.
    """
    try:
        type_args = t.__args__  # type: ignore
        return (
            not _is_optional(t)
            and all(map(lambda x: isinstance(x, type), type_args))
            and type_name(t).startswith("typing.Union")
        )
    except Exception:
        return False
