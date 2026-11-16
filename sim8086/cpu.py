"""The 8086 CPU: 16-bit registers, flags and 64 KB of flat memory."""
from .isa import REG16


class SimError(Exception):
    """Raised when the program does something impossible while running."""


def _parity(v):
    return bin(v & 0xFF).count("1") % 2 == 0


class CPU:
    def __init__(self, program):
        self.prog = program
        self.regs = {r: 0 for r in REG16}
        self.mem = bytearray(65536)
        self.flags = {"CF": 0, "ZF": 0, "SF": 0, "OF": 0, "PF": 0}
        self.ip = 0
        self.halted = False
        self.steps = 0

    # ---------------- registers ----------------
    def get_reg(self, name):
        if name in self.regs:
            return self.regs[name]
        base = self.regs[name[0] + "X"]
        return base & 0xFF if name[1] == "L" else base >> 8

    def set_reg(self, name, value):
        if name in self.regs:
            self.regs[name] = value & 0xFFFF
            return
        key = name[0] + "X"
        if name[1] == "L":
            self.regs[key] = (self.regs[key] & 0xFF00) | (value & 0xFF)
        else:
            self.regs[key] = (self.regs[key] & 0x00FF) | ((value & 0xFF) << 8)

    # ---------------- memory ----------------
    def ea(self, op):
        _, regs, disp, _ = op
        return (sum(self.regs[r] for r in regs) + disp) & 0xFFFF

    def mem_read(self, addr, size):
        n = size // 8
        return int.from_bytes(bytes(self.mem[(addr + i) & 0xFFFF] for i in range(n)), "little")

    def mem_write(self, addr, size, value):
        for i, b in enumerate((value & ((1 << size) - 1)).to_bytes(size // 8, "little")):
            self.mem[(addr + i) & 0xFFFF] = b

    # ---------------- operands ----------------
    def size_of(self, *ops):
        for o in ops:
            if o[0] == "reg":
                return o[2]
        for o in ops:
            if o[0] == "mem" and o[3]:
                return o[3]
        raise SimError("operand size unknown - write 'byte' or 'word', e.g. MOV word [SI], 5")

    def read(self, op, size):
        kind = op[0]
        if kind == "reg":
            return self.get_reg(op[1])
        if kind == "imm":
            return op[1] & ((1 << size) - 1)
        if kind == "mem":
            return self.mem_read(self.ea(op), size)
        raise SimError("cannot read a label")

    def write(self, op, size, value):
        if op[0] == "reg":
            self.set_reg(op[1], value)
        elif op[0] == "mem":
            self.mem_write(self.ea(op), size, value)
        else:
            raise SimError("cannot write to this operand")

    # ---------------- flags ----------------
    def set_szp(self, res, size):
        mask = (1 << size) - 1
        self.flags["ZF"] = int((res & mask) == 0)
        self.flags["SF"] = (res >> (size - 1)) & 1
        self.flags["PF"] = int(_parity(res))

    def do_add(self, a, b, size):
        mask, sign = (1 << size) - 1, 1 << (size - 1)
        res = (a + b) & mask
        self.flags["CF"] = int(a + b > mask)
        self.flags["OF"] = int(bool(~(a ^ b) & (a ^ res) & sign))
        self.set_szp(res, size)
        return res

    def do_sub(self, a, b, size):
        mask, sign = (1 << size) - 1, 1 << (size - 1)
        res = (a - b) & mask
        self.flags["CF"] = int(a < b)
        self.flags["OF"] = int(bool((a ^ b) & (a ^ res) & sign))
        self.set_szp(res, size)
        return res

    def do_logic(self, res, size):
        self.flags["CF"] = self.flags["OF"] = 0
        self.set_szp(res, size)
        return res

    # ---------------- jumps ----------------
    def condition(self, name):
        f = self.flags
        cf, zf, sf, of, pf = f["CF"], f["ZF"], f["SF"], f["OF"], f["PF"]
        table = {
            "JE": zf, "JZ": zf, "JNE": not zf, "JNZ": not zf,
            "JA": not cf and not zf, "JNBE": not cf and not zf,
            "JAE": not cf, "JNB": not cf, "JNC": not cf,
            "JB": cf, "JNAE": cf, "JC": cf,
            "JBE": cf or zf, "JNA": cf or zf,
            "JG": not zf and sf == of, "JNLE": not zf and sf == of,
            "JGE": sf == of, "JNL": sf == of,
            "JL": sf != of, "JNGE": sf != of,
            "JLE": zf or sf != of, "JNG": zf or sf != of,
            "JS": sf, "JNS": not sf, "JO": of, "JNO": not of,
            "JP": pf, "JPE": pf, "JNP": not pf, "JPO": not pf,
        }
        return bool(table[name])

    def jump(self, label):
        self.ip = self.prog.labels[label[1]]

    # ---------------- one instruction ----------------
    def step(self):
        ins = self.prog.instrs[self.ip]
        op, a = ins.op, ins.args
        self.ip += 1
        self.steps += 1
        try:
            self.execute(op, a)
        except SimError as e:
            raise SimError(f"line {ins.line} ({ins.text}): {e}") from None

    def execute(self, op, a):
        if op == "HLT":
            self.halted = True
        elif op == "NOP":
            pass
        elif op == "MOV":
            size = self.size_of(a[0], a[1])
            self.write(a[0], size, self.read(a[1], size))
        elif op == "XCHG":
            size = self.size_of(a[0], a[1])
            x, y = self.read(a[0], size), self.read(a[1], size)
            self.write(a[0], size, y)
            self.write(a[1], size, x)
        elif op in ("ADD", "SUB", "CMP", "AND", "OR", "XOR"):
            size = self.size_of(a[0], a[1])
            x, y = self.read(a[0], size), self.read(a[1], size)
            if op == "ADD":
                res = self.do_add(x, y, size)
            elif op in ("SUB", "CMP"):
                res = self.do_sub(x, y, size)
            elif op == "AND":
                res = self.do_logic(x & y, size)
            elif op == "OR":
                res = self.do_logic(x | y, size)
            else:
                res = self.do_logic(x ^ y, size)
            if op != "CMP":
                self.write(a[0], size, res)
        elif op in ("INC", "DEC"):
            size = self.size_of(a[0])
            x = self.read(a[0], size)
            cf = self.flags["CF"]                       # INC/DEC keep the carry flag
            res = self.do_add(x, 1, size) if op == "INC" else self.do_sub(x, 1, size)
            self.flags["CF"] = cf
            self.write(a[0], size, res)
        elif op == "NOT":
            size = self.size_of(a[0])
            self.write(a[0], size, ~self.read(a[0], size))
        elif op == "NEG":
            size = self.size_of(a[0])
            x = self.read(a[0], size)
            res = self.do_sub(0, x, size)
            self.write(a[0], size, res)
        elif op in ("SHL", "SHR"):
            size = self.size_of(a[0])
            x = self.read(a[0], size)
            count = (self.get_reg("CL") if a[1][0] == "reg" else a[1][1]) & 0x1F
            if count:
                mask = (1 << size) - 1
                if op == "SHL":
                    self.flags["CF"] = (x >> (size - count)) & 1 if count <= size else 0
                    x = (x << count) & mask
                else:
                    self.flags["CF"] = (x >> (count - 1)) & 1
                    x >>= count
                self.set_szp(x, size)
                self.write(a[0], size, x)
        elif op == "PUSH":
            self.regs["SP"] = (self.regs["SP"] - 2) & 0xFFFF
            self.mem_write(self.regs["SP"], 16, self.read(a[0], 16))
        elif op == "POP":
            self.write(a[0], 16, self.mem_read(self.regs["SP"], 16))
            self.regs["SP"] = (self.regs["SP"] + 2) & 0xFFFF
        elif op == "MUL":
            size = self.size_of(a[0])
            src = self.read(a[0], size)
            if size == 16:
                res = self.regs["AX"] * src
                self.regs["AX"], self.regs["DX"] = res & 0xFFFF, res >> 16
                self.flags["CF"] = self.flags["OF"] = int(res >> 16 != 0)
            else:
                res = self.get_reg("AL") * src
                self.regs["AX"] = res & 0xFFFF
                self.flags["CF"] = self.flags["OF"] = int(res >> 8 != 0)
        elif op == "DIV":
            size = self.size_of(a[0])
            src = self.read(a[0], size)
            if src == 0:
                raise SimError("divide by zero")
            if size == 16:
                dividend = (self.regs["DX"] << 16) | self.regs["AX"]
                q, r = divmod(dividend, src)
                if q > 0xFFFF:
                    raise SimError("divide overflow")
                self.regs["AX"], self.regs["DX"] = q, r
            else:
                q, r = divmod(self.regs["AX"], src)
                if q > 0xFF:
                    raise SimError("divide overflow")
                self.regs["AX"] = (r << 8) | q
        elif op == "JMP":
            self.jump(a[0])
        elif op == "LOOP":
            self.regs["CX"] = (self.regs["CX"] - 1) & 0xFFFF
            if self.regs["CX"] != 0:
                self.jump(a[0])
        elif op == "JCXZ":
            if self.regs["CX"] == 0:
                self.jump(a[0])
        else:                                            # conditional jumps
            if self.condition(op):
                self.jump(a[0])

    # ---------------- run ----------------
    def run(self, max_steps=1_000_000, trace=False):
        while not self.halted and self.ip < len(self.prog.instrs):
            if self.steps >= max_steps:
                raise SimError(f"stopped after {max_steps} steps - is there an endless loop?")
            ins = self.prog.instrs[self.ip]
            self.step()
            if trace:
                r = self.regs
                print(f"{ins.line:>4}: {ins.text:<28} AX={r['AX']:04X} BX={r['BX']:04X} "
                      f"CX={r['CX']:04X} DX={r['DX']:04X} SI={r['SI']:04X} "
                      f"ZF={self.flags['ZF']} CF={self.flags['CF']}")
        return self.steps
