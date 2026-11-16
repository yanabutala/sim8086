import argparse
import sys

from .assembler import assemble, AsmError, parse_number
from .cpu import CPU, SimError


def number(text):
    n = parse_number(text)
    if n is None:
        raise argparse.ArgumentTypeError(f"'{text}' is not a number")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim8086", description="Run 8086 assembly programs.")
    ap.add_argument("file", help="assembly source file (.asm)")
    ap.add_argument("--dump", nargs=2, metavar=("START", "LENGTH"), type=number, action="append",
                    help="show memory after the run, e.g. --dump 0500h 40")
    ap.add_argument("--words", action="store_true", help="also show dumped memory as 16-bit numbers")
    ap.add_argument("--trace", action="store_true", help="print every instruction as it runs")
    ap.add_argument("--max-steps", type=int, default=1_000_000, help="stop endless loops (default 1000000)")
    args = ap.parse_args(argv)

    try:
        with open(args.file, encoding="utf-8") as f:
            program = assemble(f.read())
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except AsmError as e:
        print(f"Compile error: {e}", file=sys.stderr)
        return 1

    cpu = CPU(program)
    try:
        steps = cpu.run(max_steps=args.max_steps, trace=args.trace)
    except SimError as e:
        print(f"Run error: {e}", file=sys.stderr)
        return 1

    print(f"Program finished ({steps} instructions executed).\n")
    r = cpu.regs
    print("Registers:")
    print(f"  AX={r['AX']:04X}  BX={r['BX']:04X}  CX={r['CX']:04X}  DX={r['DX']:04X}")
    print(f"  SI={r['SI']:04X}  DI={r['DI']:04X}  BP={r['BP']:04X}  SP={r['SP']:04X}")
    print("Flags: " + "  ".join(f"{k}={v}" for k, v in cpu.flags.items()))

    for start, length in args.dump or []:
        print(f"\nMemory from {start:04X}h ({length} bytes):")
        for off in range(0, length, 16):
            chunk = cpu.mem[start + off: start + min(off + 16, length)]
            print(f"  {start + off:04X}: " + " ".join(f"{b:02X}" for b in chunk))
        if args.words:
            words = [cpu.mem_read(start + i, 16) for i in range(0, length - 1, 2)]
            print("  As 16-bit numbers: " + ", ".join(str(w) for w in words))
    return 0


if __name__ == "__main__":
    sys.exit(main())
