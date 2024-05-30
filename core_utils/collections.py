from typing import Iterable, Iterator, Sequence, TypeVar, Union

from core_utils.serialization import is_namedtuple

__all__: Sequence[str] = (
    "Nested",
    "flatten",
    "is_flattenable",
)

T = TypeVar("T")

Nested = Iterable[Union[T, "Nested"]]
"""Type representing an arbitrary level of nested values.
"""


def flatten(elements: Nested, preserve_tuple: bool = False) -> Iterator[T]:
    """Flattens an arbitrarily-deeply-nested iterable of iterables.

    Uses :func:`is_flattenable` to control what explict types are able to be flattened.
    Additionally, any `None` values from within the input `elements` will be filtered-out from the
    final output iterable.

    The flag, `preserve_tuple`, controls whether or not `tuple` instances are flattened.
    By default, this flag is `False`, meaning that `tuples` are flattned out. I.e. a `List[tuple]`
    will be transformed into an `Iterable` of all of the individual elements from all `tuple`s in
    the `list`.

    If this parameter is `True`, then any `tuple` instance encountered is treated as indivisible.
    However, note that all `NamedTuple` instances are always indivisible: they are treated as
    encapsulated objects, not as an `Iterable` thing.
    """
    if is_flattenable(elements):
        # The `for` construct iterates over _every_ iterable.
        for elem in elements:
            if elem is not None:
                if preserve_tuple and isinstance(elem, tuple):
                    yield elem

                elif is_flattenable(elem):
                    # flatten(elem, ...) will continue to un-roll the nested structure
                    for sub_elem in flatten(elem, preserve_tuple=preserve_tuple):
                        yield sub_elem
                else:
                    yield elem
    else:
        raise ValueError(f"flatten only accepts an iterable, not: {type(elements)}")


def is_flattenable(x) -> bool:
    """Test to see if a value is acceptable for the :func:`flatten` higher-order-function.

    If `True`, then the input is acceptable by :func:`flatten`. `False` otherwise.
    The following common types are flattenable:
      - `list`
      - `Iterator` (includes generators, iterators, map, filter)
      - tuple (but not a namedtuple - uses :func:`is_namedtuple` to check)
      - `set`
      - `range` (e.g. `range(10)` is accepted)`

    Note that the follown common types *ARE NOT* flattenable:
      - `dict`
    """
    return (not isinstance(x, dict)) and (
        isinstance(x, list)
        or isinstance(x, Iterator)
        or (isinstance(x, tuple) and not is_namedtuple(x))
        or isinstance(x, set)
        or isinstance(x, range)
    )
