import os.path
import re
from io import StringIO

from .core import SystemCall, SystemCallParameter

# NOTE: a problem with this implementation is that it doesn't, and cannot take into account system call declarations that are inside #if and #ifdefs, such as sys_clone(). Currently this (in kernel version 4.4.0-67-generic) this doesn't seem to pose a problem (besides issuing some -Woverride-init warnings), but it's something to be considered.

def parse_syscalls_h(file_path):
  # System calls are defined similarly to this:
  #
  #   asmlinkage long sys_io_getevents(aio_context_t ctx_id,
  #           long min_nr,
  #           long nr,
  #           struct io_event __user *events,
  #           struct timespec __user *timeout);

  FUNC_START_PATTERN = re.compile('^asmlinkage (.*?) sys[_](.*?)[(]')
  PARAM_NAME_PATTERN = re.compile('^[a-zA-Z_][a-zA-Z_0-9]*$')

  def separate_parameters(text):
    param_buffer = StringIO()

    for c in text:
      if c == ")":
        # the function declaration is over, we're done
        yield param_buffer.getvalue().strip()
        yield True # indicate we're completely done
        return
      elif c == ",":
        # the parameter is done
        yield param_buffer.getvalue().strip()

        # reset the buffer before continuing
        param_buffer.truncate(0)
        param_buffer.seek(0)
      else:
        param_buffer.write(c)

    # indicate that we haven't encountered a ), parsing should continue in the next line
    yield False


  def is_parameter_type(text):
    return text.endswith("_t") \
      or text in [ "int", "long", "short", "char", "const" ]


  def is_incomplete_parameter_type(text):
    return text in [ "struct", "enum", "union", "const", "volatile" ]


  def parse_parameter(param_text):
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
      raise NotImplementedError("Unable to parse parameter '{}': parsed name '{}' seems invalid!".format(param_text, param_name))

    # sometimes the parameter name is missing, but the type is multiple words - try to detect these cases and fix them
    if param_name is not None:
      param_name = param_name.strip()

      if is_parameter_type(param_name) or is_incomplete_parameter_type(param_type):
        param_type += " " + param_name
        param_name = None

    # don't emit the "no parameters" pseudo-parameter, e.g. gettid(void)
    if param_type == "void" and param_name is None:
      return None

    return SystemCallParameter(param_name, param_type)


  # -- end helper functions

  # TODO: instead of a list, use a dictionary or something
  syscalls = []

  with open(file_path, "r") as fp:
    current_syscall = None

    for line in fp.readlines():
      params_text = None

      if current_syscall is None:
        m = FUNC_START_PATTERN.match(line)
        if m is None:
          continue

        return_type = m.group(1)
        name = m.group(2)

        current_syscall = SystemCall(name, return_type)

        params_text = line[len(m.group(0)) :]
      else:
        params_text = line

      # parse parameters
      for param_text in separate_parameters(params_text):
        if param_text is False:
          # we're finished with parsing the line, but not finished with parsing the syscall declaration
          break
        elif param_text is True:
          # we're done with parsing this syscall declaration
          syscalls.append(current_syscall)
          current_syscall = None
          break
        else:
          param = parse_parameter(param_text)
          if param is not None:
            current_syscall.add_param(param)

  return syscalls


def load_from_headers(linux_headers_path):
  header_path = os.path.join(linux_headers_path, "include", "linux", "syscalls.h")
  return parse_syscalls_h(header_path)