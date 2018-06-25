class SystemCallParameter:
  def __init__(self, name, ty):
    self._name = name
    self._type = ty

  @property
  def name(self):
    return self._name

  @property
  def type(self):
    return self._type

  @property
  def is_anonymous(self):
    return self.name is None

  @property
  def is_user_pointer(self):
    return self.type.endswith("__user *")


class SystemCall:
  def __init__(self, name, return_type):
    self._name = name.strip()
    self._return_type = return_type.strip()
    self._params = []

  @property
  def name(self):
    return self._name

  @property
  def return_type(self):
    return self._return_type

  @property
  def params(self):
    return self._params

  @property
  def num_params(self):
    return len(self.params)

  def add_param(self, param):
    self._params.append(param)

  @property
  def number_macro(self):
    return "__NR_{}".format(self.name)
