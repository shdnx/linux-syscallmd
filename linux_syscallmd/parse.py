import os.path
import re
from io import StringIO
from typing import List, NamedTuple

from .model import SystemCall, SystemCallParameter

# NOTE: a problem with this implementation is that it doesn't, and cannot take into account system call declarations that are inside #if and #ifdefs, such as sys_clone(). Currently this (in kernel version 4.4.0-67-generic) this doesn't seem to pose a problem (besides issuing some -Woverride-init warnings), but it's something to be considered.

def parse_syscalls_h(file_path: str) -> List[SystemCall]:
  # System calls are defined similarly to this:
  #
  #   asmlinkage long sys_io_getevents(aio_context_t ctx_id,
  #           long min_nr,
  #           long nr,
  #           struct io_event __user *events,
  #           struct timespec __user *timeout);

  FUNC_START_PATTERN = re.compile(r'^asmlinkage (?P<return_type>.*?) sys[_](?P<name>.*?)[(]')


  def is_parameter_type(text: str) -> bool:
    return text.endswith("_t") \
      or text in [ "int", "long", "short", "char", "const" ]


  def is_incomplete_parameter_type(text: str) -> bool:
    return text in [ "struct", "enum", "union", "const", "volatile" ]


  def parse_parameter(param_text: str) -> SystemCallParameter:
    PARAM_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z_0-9]*$')

    param_text = param_text.strip()
    param_type = None
    param_name = None

    # this wouldn't work for complicated things like function types or array types, but it's fine for the simpler cases, and system calls will never take complicated things as parameters
    last_space_index = param_text.rfind(" ")
    if last_space_index == -1:
      param_type = param_text
    else:
      param_type = param_text[: last_space_index].strip()
      param_name = param_text[last_space_index + 1 :].strip()

      if param_name[0] == "*":
        param_type += " *"
        param_name = param_name[1:]

      if param_name == "":
        param_name = None

    if param_name is not None and PARAM_NAME_PATTERN.match(param_name) is None:
      raise NotImplementedError(f"Unable to parse parameter '{param_text}': parsed name '{param_name}' seems invalid!")

    # sometimes the parameter name is missing, but the type is multiple words - try to detect these cases and fix them
    if param_name is not None:
      param_name = param_name.strip()

      if is_parameter_type(param_name) or is_incomplete_parameter_type(param_type):
        param_type += " " + param_name
        param_name = None

    # don't emit the "no parameters" pseudo-parameter, e.g. gettid(void)
    if param_type == "void" and param_name is None:
      return None

    return SystemCallParameter(
      name = param_name,
      type = param_type
    )


  def handle_syscall_parameter(
    syscall: SystemCall,
    param_buffer: StringIO
  ) -> None:
    param_text = param_buffer.getvalue().strip()

    # reset the buffer before continuing
    param_buffer.truncate(0)
    param_buffer.seek(0)

    param = parse_parameter(param_text)
    if param is not None:
      syscall.params.append(param)


  # TODO: instead of a list, use a dictionary or something
  syscalls = []

  with open(file_path, "r") as fp:
    current_syscall = None

    param_buffer = StringIO()

    for line in fp:
      params_text_to_parse = line

      # if we're not currently parsing a system call, try beginning to parse one
      if current_syscall is None:
        m = FUNC_START_PATTERN.match(line)
        if m is None:
          continue

        current_syscall = SystemCall(
          name = m.group("name").strip(),
          return_type = m.group("return_type").strip(),
          params = []
        )
        syscalls.append(current_syscall)

        params_text_to_parse = line[len(m.group(0)) :]

      # parse parameters
      for c in params_text_to_parse:
        if c == "\n":
          continue
        elif c == "\t":
          param_buffer.write(' ')
        elif c == ")":
          # NOTE: this wouldn't work if e.g. multi-parameter macros or function types were used in syscall declarations
          handle_syscall_parameter(current_syscall, param_buffer)
          current_syscall = None
          break
        elif c == ",":
          handle_syscall_parameter(current_syscall, param_buffer)
        else:
          param_buffer.write(c)

  return syscalls


def load_from_headers(linux_headers_path: str) -> List[SystemCall]:
  header_path = os.path.join(linux_headers_path, "include", "linux", "syscalls.h")
  return parse_syscalls_h(header_path)
