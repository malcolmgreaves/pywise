from core_utils.serialization import serialize, deserialize
from dataclasses import dataclass
from typing import *

@dataclass(frozen=True)
class A:
    a: int

@dataclass(frozen=True)
class B:
    b: str

@dataclass(frozen=True)
class C:
    c: Union[A, B, List[A], List[B], Mapping[int, str]]


#print(get_origin(Mapping[int,str]))

#print(get_args(Mapping[int,str]))

#print(get_origin(Dict[int,str]))


#print(get_origin(Optional[int]))


T = TypeVar('T')

@dataclass(frozen=True)
class G(Generic[T]):
    item: T
    

x: G[int] = G(1)

#print(f"{x=}")

#print(f"{get_origin(G[int])=}")

#print(f"{get_args(G[int])=}")

print(f"{deserialize(C, serialize(C(A(1))))=}")

print(f"{deserialize(C, serialize(C([A(1)])))=}")

print(f"{deserialize(C, serialize(C([B('ss')])))=}")

print(f"{deserialize(C, serialize(C([A(1), A(2), A(4)])))=}")

print(f"{deserialize(C, serialize(C({1: 'hello'})))=}")
