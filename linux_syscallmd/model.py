from typing import List, NamedTuple

class SystemCallParameter(NamedTuple):
  name: str
  type: str

  @property
  def is_anonymous(self) -> bool:
    return self.name is None

  @property
  def is_user_pointer(self) -> bool:
    return self.type.endswith("__user *")


class SystemCall(NamedTuple):
  name: str
  return_type: str
  params: List[SystemCallParameter]

  @property
  def number_macro(self) -> str:
    return f"__NR_{self.name}"
