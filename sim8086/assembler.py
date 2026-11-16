"""Turns 8086 assembly text into a list of instructions the CPU can run.

Operands become tuples:
    ("reg", "AX", 16)                    register and its size in bits
    ("imm", 123)                         number
    ("mem", ["SI"], 2, 16)               [SI+2], size 16 (or None if not given)
    ("label", "LOOP1")                   jump target
"""
import re
from dataclasses import dataclass, field

from .isa import REG16, REG8, ADDR_REGS, MNEMONICS, ZERO_OPS, ONE_OP, TWO_OPS, JUMPS


class AsmError(Exception):
    """Raised when the source code has a mistake."""


@dataclass
class Instr:
    op: str
    args: list
    line: int
    text: str


@dataclass
class Program:
    instrs: list = field(default_factory=list)
    labels: dict = field(default_factory=dict)


def parse_number(tok):
    """Return an int for 123, 0500h, 0x500, 1010b, 'A' ... or None."""
    t = tok.strip()
    if re.fullmatch(r"'.'", t):
        return ord(t[1])
    t = t.lower()
    sign = 1
    if t.startswith("-"):
        sign, t = -1, t[1:]
    elif t.startswith("+"):
        t = t[1:]
    if re.fullmatch(r"0x[0-9a-f]+", t):
        v = int(t, 16)
    elif re.fullmatch(r"[0-9][0-9a-f]*h", t):
        v = int(t[:-1], 16)
    elif re.fullmatch(r"[01]+b", t):
        v = int(t[:-1], 2)
    elif re.fullmatch(r"\d+", t):
        v = int(t)
    else:
        return None
    return sign * v


def strip_comment(line):
    out, quote = [], False
    for ch in line:
        if ch == "'":
            quote = not quote
        if ch == ";" and not quote:
            break
        out.append(ch)
    return "".join(out).strip()


def parse_memory(inner, size, lineno):
    regs, disp = [], 0
    terms = re.findall(r"[+-]?[^+-]+", inner.replace(" ", ""))
    if not terms or "".join(terms) != inner.replace(" ", ""):
        raise AsmError(f"line {lineno}: bad memory operand [{inner}]")
    for term in terms:
        sign = -1 if term.startswith("-") else 1
        body = term.lstrip("+-")
        if body.upper() in ADDR_REGS:
            if sign < 0:
                raise AsmError(f"line {lineno}: cannot subtract a register in [{inner}]")
            regs.append(body.upper())
        else:
            n = parse_number(body)
            if n is None:
                raise AsmError(f"line {lineno}: '{body}' is not a number or one of BX/BP/SI/DI")
            disp += sign * n
    if len(regs) > 2:
        raise AsmError(f"line {lineno}: too many registers in [{inner}]")
    return ("mem", regs, disp, size)


def parse_operand(text, lineno):
    t = text.strip()
    m = re.fullmatch(r"(?:(byte|word)\s+(?:ptr\s+)?)?\[(.+)\]", t, re.I)
    if m:
        size = None
        if m.group(1):
            size = 8 if m.group(1).lower() == "byte" else 16
        return parse_memory(m.group(2), size, lineno)
    up = t.upper()
    if up in REG16:
        return ("reg", up, 16)
    if up in REG8:
        return ("reg", up, 8)
    n = parse_number(t)
    if n is not None:
        return ("imm", n)
    if re.fullmatch(r"[A-Za-z_.$][\w.$]*", t):
        return ("label", up)
    raise AsmError(f"line {lineno}: cannot understand operand '{t}'")


def assemble(source):
    prog = Program()
    pending_jumps = []
    for lineno, raw in enumerate(source.splitlines(), start=1):
        line = strip_comment(raw)
        # labels:  name:   (may be followed by an instruction)
        while True:
            m = re.match(r"^([A-Za-z_.$][\w.$]*)\s*:\s*(.*)$", line)
            if not m:
                break
            name = m.group(1).upper()
            if name in prog.labels:
                raise AsmError(f"line {lineno}: label '{m.group(1)}' defined twice")
            prog.labels[name] = len(prog.instrs)
            line = m.group(2).strip()
        if not line:
            continue

        parts = line.split(None, 1)
        op = parts[0].upper()
        if op not in MNEMONICS:
            raise AsmError(f"line {lineno}: unknown instruction '{parts[0]}'")
        rest = parts[1] if len(parts) > 1 else ""
        texts = [x for x in rest.split(",")] if rest.strip() else []
        args = [parse_operand(x, lineno) for x in texts]

        want = 0 if op in ZERO_OPS else 1 if op in ONE_OP else 2
        if len(args) != want:
            raise AsmError(f"line {lineno}: {op} needs {want} operand(s), found {len(args)}")
        if op in JUMPS:
            if args[0][0] != "label":
                raise AsmError(f"line {lineno}: {op} needs a label")
            pending_jumps.append((args[0][1], lineno))
        prog.instrs.append(Instr(op, args, lineno, line))

    for name, lineno in pending_jumps:
        if name not in prog.labels:
            raise AsmError(f"line {lineno}: label '{name.lower()}' is not defined")
    return prog
