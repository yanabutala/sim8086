# sim8086

A small **8086 assembler and simulator** written in Python. Write 8086 assembly,
run it from the command line, and look at the registers, flags and memory
afterwards - like the online 8086 simulators, but on your own computer.

It reads the assembly text, checks it for mistakes (with line numbers), and then
runs it instruction by instruction on a simulated 8086 (16-bit registers, flags
and 64 KB of memory). It needs **Python 3.8+ and nothing else**.

## Quick start

```bash
git clone https://github.com/yanabutala/sim8086.git
cd sim8086
python -m sim8086 examples/bubble_sort.asm --dump 0500h 40 --words
```

Output:

```
Program finished (2834 instructions executed).

Registers:
  AX=EA60  BX=FDE8  CX=0000  DX=0000
  SI=0526  DI=0000  BP=0000  SP=0000
Flags: CF=0  ZF=1  SF=0  OF=0  PF=1

Memory from 0500h (40 bytes):
  0500: 03 00 09 00 0F 00 12 00 4D 00 7B 00 FA 00 00 01
  ...
  As 16-bit numbers: 3, 9, 15, 18, 77, 123, 250, 256, 500, 872, 999, 1500, ...
```

## Command-line options

| Option | Meaning |
|---|---|
| `--dump START LENGTH` | Show memory after the run, e.g. `--dump 0500h 40` (can be repeated) |
| `--words` | Also show the dumped memory as 16-bit numbers |
| `--trace` | Print every instruction with the registers as it runs |
| `--max-steps N` | Stop after N instructions (default 1,000,000) to catch endless loops |

## Supported language

* **Registers:** `AX BX CX DX SI DI BP SP` and `AL AH BL BH CL CH DL DH`
* **Instructions:** `MOV XCHG ADD SUB CMP AND OR XOR INC DEC NOT NEG SHL SHR MUL DIV PUSH POP LOOP JMP JCXZ HLT NOP`
* **Jumps:** `JE JZ JNE JNZ` · unsigned `JA JAE JB JBE JC JNC` · signed `JG JGE JL JLE` · `JS JNS JO JNO JP JNP`
* **Memory operands:** `[1280]`, `[SI]`, `[SI+2]`, `[BX+SI+4]`, with `byte` or `word` in front, e.g. `MOV word [SI], 4500`
* **Numbers:** decimal `1280`, hex `0500h` or `0x500`, binary `1010b`, characters `'A'`
* **Labels** (`next:`) and `;` comments

The size (`byte`/`word`) is taken from a register operand. When you store a
number straight into memory you must write it: `MOV word [SI], 5`.

## Limits (what this is not)

* It is an **interpreter**: it does not produce machine code or `.com`/`.exe` files.
* Memory is one flat 64 KB block (no segment registers, no `ORG`/`DB`/`DW` directives).
* No `INT` calls, no keyboard or screen I/O. Check results by dumping memory.
* Memory and registers start at 0.

## Examples

* `examples/bubble_sort.asm` - sorts twenty 16-bit unsigned numbers (uses `JBE`)
* `examples/fibonacci.asm` - stores the first 15 Fibonacci numbers from 0500h

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## How it is built

| File | Job |
|---|---|
| `sim8086/assembler.py` | Reads the text, finds labels, parses operands, reports errors |
| `sim8086/cpu.py` | Registers, flags, memory and the execution of each instruction |
| `sim8086/isa.py` | Lists of registers and instructions shared by both |
| `sim8086/__main__.py` | The command-line program |

## License

MIT - see `LICENSE`.
