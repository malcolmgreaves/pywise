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



def test():
  def f():
     yield 1
     yield 2
  
  def z():
    for x in [f,f,f,f]: yield x()
  
  assert list(yield_all(z())) == [1, 2, 1, 2, 1, 2, 1, 2]
  
  def a():
    for x in [z,z,z,z]: yield x()
  
  def b():
    for x in [a,a,a,a]: yield x()
  
  assert list(yield_all(b())) == [1,2] * 64
