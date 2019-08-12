print("importing module linux_syscallmd")
import linux_syscallmd

linux_headers_dir = "/usr/src/linux-headers-4.4.0-67-generic"

print(f"calling load_from_headers('{linux_headers_dir}')")

syscalls = linux_syscallmd.load_from_headers(linux_headers_dir)

print(f"{len(syscalls)} results - check the 'syscalls' variable")
