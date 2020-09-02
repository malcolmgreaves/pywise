from typing import Union, Iterator, TypeVar

T = TypeVar('T')


def yield_all(elements: Iterator[Union[T, Iterator[T]]]) -> Iterator[T]:
    """Yields individual elements from any level of nested iterators.
    """
    for e in elements:
        if isinstance(e, Iterator):
            for sub_e in yield_all(e):
                yield sub_e
        else:
            yield e
