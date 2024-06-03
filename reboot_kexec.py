#! /usr/env/bin python
import sys
from subprocess import Popen, PIPE


def exec_cmd(cmd):
    print(cmd)
    with Popen(cmd, stdout=PIPE) as proc:
        out, _ = proc.communicate()
        proc.wait()
        print(out.decode('utf-8'))
        return out.decode('utf-8')


def main():
    if len(sys.argv) < 2:
        print("Error")
        return
    version = sys.argv[1]
    cmdline_old = exec_cmd("cat /proc/cmdline".split())
    cmdline = " ".join(cmdline_old.split()[1:])
    kexec_config = [
        "/sbin/kexec",
        "-l",
        f"/boot/vmlinuz-{version}",
        f"--initrd=/boot/initrd.img-{version}",
        f'--command-line=BOOT_IMAGE=/boot/vmlinuz-{version} {cmdline}'
    ]
    exec_cmd(kexec_config)
    exec_cmd("/sbin/kexec -e".split())


if __name__ == "__main__":
    main()
