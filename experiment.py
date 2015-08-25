class Foo:
  def __init__(self,a,b,c):
    self._a = a
    self._b = b
    self._c = c

  @property
  def a(self):
    return self._a

  @a.setter
  def a(self, value):
    self._a = value

  @property
  def b(self):
    return self._b

  @b.setter
  def b(self, value):
    self._b = value

  @property
  def c(self):
    return self._c

  @c.setter
  def c(self, value):
    self._c = value
