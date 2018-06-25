# Introduction

In certain, very specific types of applications, having access to metadata about the available Linux system calls is very useful. One example is intercepting system calls: in order to be able to do anything useful, you would need to figure out which system call you're dealing with, how many parameters does it take and perhaps which, if any, of those is interesting.

The motivating example for this project was [dangless-malloc](https://github.com/shdnx/dangless-malloc), which uses this information when intercepting system calls to modify userspace pointer arguments before they are passed to the kernel.

# What is this?

`linux_syscallmd` is a small Python 3 library that is capable of parsing the Linux kernel header files and collecting metadata about the available system calls.

`generate_c_header` is a Python script that, given the system call metadata collected by `linux_syscallmd`, generates a C/C++ header file that exposes that information.

# Caveats

Currently `linux_syscallmd` works by parsing the `include/linux/syscalls.h` Linux header file (see `linux_syscallmd/parse.py`). If a Linux kernel release at some point decides to move, rename or significantly change this file, the parser will probably break.

Tested and working with the following kernel versions:

 * 4.4.0-67-generic

# Requirements

 * Python 3
 * Linux kernel header files (usually found at /usr/src/linux-headers-\*)

# Documentation

## `generate_c_header.py` and its output

Given the path to the directory containing the Linux kernel header files, outputs to `stdout` a C/C++ header file that encodes the system call metadata information through a series of macro expansions. These macros can be defined by the including file, allowing for code to be generated based on the system call metadata.

These macros are:

 * `SYSCALL_SIGNATURE(NUM_MACRO, NAME, NUM_PARAMS, PARAM_TYPES...)`
   * `NUM_MACRO`: a macro name that expands to the number of this system call if it's defined
   * `NAME`: the name of the system call
   * `NUM_PARAMS`: the number of parameters
   * `PARAM_TYPES...`: variadic parameters representing the types of all parameters
 * `SYSCALL_PARAM(POS, TYPE, NAME, IS_USER_PTR)`
   * `POS`: the position of the parameter (1-based)
   * `TYPE`: the full type of the parameter
   * `NAME`: the name of the parameter
   * `IS_USER_PTR`: 1 if this parameter is a userspace pointer, otehrwise 0
 * `SYSCALL_END()`: same as `SYSCALL_SIGNATURE()`

Sample:

```c
#ifdef __NR_getrandom
  SYSCALL_SIGNATURE(__NR_getrandom, getrandom, 3, char __user * /* buf */, size_t /* count */, unsigned int /* flags */)
  SYSCALL_PARAM(1, char __user *, buf, 1)
  SYSCALL_PARAM(2, size_t, count, 0)
  SYSCALL_PARAM(3, unsigned int, flags, 0)
  SYSCALL_END(__NR_getrandom, long, getrandom, 3, char __user * /* buf */, size_t /* count */, unsigned int /* flags */)
#endif
```

For an example on how to define these macros, see [`syscallmeta.c`](https://github.com/shdnx/dangless-malloc/blob/master/sources/src/syscallmeta.c) in `dangless-malloc`.

## Package `linux_syscallmd`

For creating a custom script that uses the system call metadata information, see `generate_c_header.py` as an example.

**TODO**: reference

# License

The 3-Clause BSD License, see `LICENSE`.
