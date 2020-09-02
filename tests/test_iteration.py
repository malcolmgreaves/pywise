from core_utils.iteration import yield_all


def test_yield_all():
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
