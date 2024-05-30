from typing import Any, NamedTuple, Optional

from pytest import raises

from core_utils.collections import flatten, is_flattenable

NT = NamedTuple("NT", [("name", str)])


def test_flatten_deep_edge_cases():
    assert list(flatten([])) == []
    assert list(flatten(tuple())) == []
    assert list(flatten(set())) == []
    assert list(flatten(range(0, 0))) == []
    assert list(flatten(map(lambda x: x, []))) == []
    assert list(flatten(filter(lambda x: True, []))) == []


def test_flatten_one_level():
    def simple_generator(limit=5):
        for i in range(limit):
            yield i

    def _help_t_flatten_one_level(
        input_, output: Optional = None, to_structure: Any = list, is_gen: bool = False
    ):
        if is_gen:
            input_ = list(input_)
        if output is None:
            output = input_
        assert to_structure(flatten(input_)) == output
        assert to_structure(flatten(input_, preserve_tuple=True)) == output

    _help_t_flatten_one_level([1])
    _help_t_flatten_one_level([10, 20, 30])
    _help_t_flatten_one_level({10, 20, 30, 40, 50}, to_structure=set)
    _help_t_flatten_one_level(range(10), output=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    _help_t_flatten_one_level(["hh", "ee", "ll", "ll", "oo"])
    _help_t_flatten_one_level((1, 2, 3), to_structure=tuple)
    _help_t_flatten_one_level(range(3), output=(0, 1, 2), to_structure=tuple)
    _help_t_flatten_one_level(simple_generator(), output=[0, 1, 2, 3, 4], is_gen=True)
    _help_t_flatten_one_level(map(lambda x: x * 10, range(4)), output=[0, 10, 20, 30], is_gen=True)
    _help_t_flatten_one_level(
        filter(lambda x: x % 2 == 0, range(10)), output=[0, 2, 4, 6, 8], is_gen=True
    )


def test_flatten_deep_nested():
    assert list(flatten([range(10), range(10, 15), range(15, 30)])) == list(range(30))

    multi_level_nested = [
        [range(10), range(10, 15), range(15, 30)],
        [range(30, 40)],
        [
            [range(40, 50), [[[[range(50, 60)]]]]],
            [
                [
                    [[[[[[[[[[[[[[[[range(60, 70)]]]]]]]]]]]]]]]],
                    [[range(70, 80)], [[[[range(80, 90)]]]]],
                    [[range(90, 100), range(100, 100)]],
                ]
            ],
        ],
    ]
    assert list(flatten(multi_level_nested)) == list(range(100))


def test_flatten_ok_namedtuple_and_tuples():
    nts = [NT("first"), NT("second"), [NT("third")]]
    assert list(flatten(nts)) == [NT("first"), NT("second"), NT("third")]
    assert list(flatten(nts, preserve_tuple=True)) == [NT("first"), NT("second"), NT("third")]

    a_tuple = (1, (2, 3), 4)
    assert tuple(flatten(a_tuple)) == (1, 2, 3, 4)
    assert tuple(flatten(a_tuple, preserve_tuple=True)) == (1, (2, 3), 4)


def test_flatten_notuple():
    input_ = [[("h", 1), ("e", 2), ("l", 3)], [("l", 4)], ("o", 5)]

    expected = [("h", 1), ("e", 2), ("l", 3), ("l", 4), ("o", 5)]

    actual_shallow = list(flatten(input_, preserve_tuple=True))
    assert actual_shallow == expected

    actual_deep = list(flatten(input_))
    assert not (actual_deep == expected)


def test_is_flattenable():
    def a_generator():
        yield 1
        yield 2
        yield 3

    assert is_flattenable([1, 2, 3])
    assert is_flattenable(a_generator())
    assert is_flattenable((1, 2, 3))
    assert is_flattenable({1, 2, 3})
    assert is_flattenable(range(1, 4))

    assert not is_flattenable(None)
    assert not is_flattenable(NT(name="hello world"))
    assert not is_flattenable("strings are not flattenable")


def test_flatten_fails():
    with raises(ValueError):
        flatten({"hello": "world"})
