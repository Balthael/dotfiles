from __future__ import annotations

import argparse
import math
import os

import pwndbg.aglib.arch
import pwndbg.aglib.elf
import pwndbg.aglib.symbol
import pwndbg.aglib.vmmap
import pwndbg.color.memory as M
import pwndbg.commands
from pwndbg.color import message
from pwndbg.commands import CommandCategory


def find_module(addr, max_distance):
    mod_filter = lambda page: page.start <= addr < page.end
    pages = list(filter(mod_filter, pwndbg.aglib.vmmap.get()))

    if not pages:
        if max_distance != 0:
            mod_filter = lambda page: page.start - max_distance <= addr < page.end + max_distance
            pages = list(filter(mod_filter, pwndbg.aglib.vmmap.get()))

        if not pages:
            return None

    return pages[-1]


def satisfied_flags(require_flags, flags):
    return (require_flags & ~(flags)) == 0


def flags_str2int(flags_s):
    flag_i = 0
    if "r" in flags_s:
        flag_i |= os.R_OK
    if "w" in flags_s:
        flag_i |= os.W_OK
    if "x" in flags_s:
        flag_i |= os.X_OK
    return flag_i


parser = argparse.ArgumentParser(
    description="""
Pointer scan for possible offset leaks.
Examples:
    probeleak $rsp 0x64 - leaks 0x64 bytes starting at stack pointer and search for valid pointers
    probeleak $rsp 0x64 --max-dist 0x10 - as above, but pointers may point 0x10 bytes outside of memory page
    probeleak $rsp 0x64 --point-to libc --max-ptrs 1 --flags rwx - leaks 0x64 bytes starting at stack pointer and \
search for one valid pointer which points to a libc rwx page
""",
)
parser.add_argument("address", nargs="?", default="$sp", help="Leak memory address")
parser.add_argument("count", nargs="?", default=0x40, help="Leak size in bytes")
parser.add_argument(
    "--max-distance",
    type=int,
    default=0x0,
    help="Max acceptable distance between memory page boundary and leaked pointer",
)
parser.add_argument(
    "--point-to",
    type=str,
    default=None,
    help="Mapping name of the page that you want the pointers point to",
)
parser.add_argument(
    "--max-ptrs", type=int, default=0, help="Stop search after find n pointers, default 0"
)
parser.add_argument(
    "--flags",
    type=str,
    default=None,
    help="flags of the page that you want the pointers point to. [e.g. rwx]",
)


@pwndbg.commands.Command(parser, category=CommandCategory.MEMORY)
@pwndbg.commands.OnlyWhenRunning
def probeleak(
    address=None, count=0x40, max_distance=0x0, point_to=None, max_ptrs=0, flags=None
) -> None:
    address = int(address)
    address &= pwndbg.aglib.arch.ptrmask
    ptrsize = pwndbg.aglib.arch.ptrsize
    count = max(int(count), ptrsize)
    off_zeros = int(math.ceil(math.log(count, 2) / 4))
    if flags is not None:
        require_flags = flags_str2int(flags)

    if count > address > 0x10000:  # in case someone puts in an end address and not a count (smh)
        print(
            message.warn(
                "Warning: you gave an end address, not a count. Subtracting 0x%x from the count."
                % (address)
            )
        )
        count -= address

    try:
        data = pwndbg.aglib.memory.read(address, count, partial=True)
    except pwndbg.dbg_mod.Error as e:
        print(message.error(str(e)))
        return

    if not data:
        print(
            message.error(
                f"Couldn't read memory at 0x{address:x}. See 'probeleak -h' for the usage."
            )
        )
        return

    found = False
    find_cnt = 0
    for i in range(0, len(data) - ptrsize + 1):
        p = pwndbg.aglib.arch.unpack(data[i : i + ptrsize])
        page = find_module(p, max_distance)
        if page:
            if point_to is not None and point_to not in page.objfile:
                continue
            if flags is not None and not satisfied_flags(require_flags, page.flags):
                continue
            if not found:
                print(M.legend())
                found = True

            mod_name = page.objfile
            if not mod_name:
                mod_name = "[anon]"

            if p >= page.end:
                right_text = "({}) {} + 0x{:x} + 0x{:x} (outside of the page)".format(
                    page.permstr,
                    mod_name,
                    page.memsz,
                    p - page.end,
                )
            elif p < page.start:
                right_text = "({}) {} - 0x{:x} (outside of the page)".format(
                    page.permstr,
                    mod_name,
                    page.start - p,
                )
            else:
                right_text = f"({page.permstr}) {mod_name} + 0x{p - page.start:x}"

            offset_text = "0x%0*x" % (off_zeros, i)
            p_text = "0x%0*x" % (int(ptrsize * 2), p)
            text = f"{offset_text}: {M.get(p, text=p_text)} = {M.get(p, text=right_text)}"

            symbol = pwndbg.aglib.symbol.resolve_addr(p)
            if symbol:
                text += f" ({symbol})"
            print(text)

            find_cnt += 1
            if max_ptrs != 0 and find_cnt >= max_ptrs:
                break

    if not found:
        print(message.hint(f"No leaks found at 0x{address:x}-0x{address + count:x} :("))
