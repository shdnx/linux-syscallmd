#!/usr/bin/env python3
import sys
import os.path

import linux_syscallmd

def emit_c_header(outs, syscalls):
  def emit_syscall_signature(outs, macro, syscall):
    outs.write(macro)
    outs.write("(")
    outs.write(syscall.number_macro)
    outs.write(", ")
    outs.write(syscall.name)
    outs.write(", ")
    outs.write(str(syscall.num_params))

    for param in syscall.params:
      outs.write(", ")
      outs.write(param.type)

      if not param.is_anonymous:
        outs.write(" /* ")
        outs.write(param.name)
        outs.write(" */")

    outs.write(")")


  outs.write("""#ifndef __NR_write
  #error __NR_write missing: you have to include <sys/syscall.h> before you can use this
#endif

#ifndef SYSCALL_SIGNATURE
  #define SYSCALL_SIGNATURE(NUM, RETTYPE, NAME, NUM_PARAMS, ...) /* empty */
#endif

#ifndef SYSCALL_PARAM
  #define SYSCALL_PARAM(POS, TYPE, NAME, IS_USER_PTR) /* empty */
#endif

#ifndef SYSCALL_END
  #define SYSCALL_END(NUM, RETTYPE, NAME, NUM_PARAMS, ...) /* empty */
#endif
""")

  for syscall in syscalls:
    outs.write("\n#ifdef {}\n".format(syscall.number_macro))

    # write SYSCALL_SIGNATURE()
    outs.write("\t")
    emit_syscall_signature(outs, "SYSCALL_SIGNATURE", syscall)
    outs.write("\n")

    for index, param in enumerate(syscall.params):
      outs.write("\tSYSCALL_PARAM(")
      outs.write(str(index + 1))
      outs.write(", ")
      outs.write(param.type)
      outs.write(", ")
      outs.write(param.name if param.name is not None else "ANON")
      outs.write(", ")
      outs.write("1" if param.is_user_pointer else "0")
      outs.write(")\n")

    outs.write("\t")
    emit_syscall_signature(outs, "SYSCALL_END", syscall)
    outs.write("\n")

    outs.write("#endif\n")

  outs.write("""
#undef SYSCALL_SIGNATURE
#undef SYSCALL_PARAM
#undef SYSCALL_END
""")

if __name__ == "__main__":
  linux_headers_dir = sys.argv[1]
  syscalls = linux_syscallmd.load_from_headers(linux_headers_dir)
  emit_c_header(sys.stdout, syscalls)
