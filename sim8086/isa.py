"""Constants shared by the assembler and the CPU."""

REG16 = ["AX", "CX", "DX", "BX", "SP", "BP", "SI", "DI"]
REG8 = ["AL", "CL", "DL", "BL", "AH", "CH", "DH", "BH"]
ADDR_REGS = ["BX", "BP", "SI", "DI"]          # allowed inside [ ... ]

# (name, name, ...) groups of jump mnemonics that mean the same thing
JCC = [
    "JE", "JZ", "JNE", "JNZ",
    "JA", "JNBE", "JAE", "JNB", "JNC", "JB", "JNAE", "JC", "JBE", "JNA",   # unsigned
    "JG", "JNLE", "JGE", "JNL", "JL", "JNGE", "JLE", "JNG",               # signed
    "JS", "JNS", "JO", "JNO", "JP", "JPE", "JNP", "JPO",
]

ZERO_OPS = {"HLT", "NOP"}
ONE_OP = {"INC", "DEC", "NOT", "NEG", "PUSH", "POP", "MUL", "DIV",
          "JMP", "LOOP", "JCXZ"} | set(JCC)
TWO_OPS = {"MOV", "ADD", "SUB", "CMP", "AND", "OR", "XOR", "XCHG", "SHL", "SHR"}
JUMPS = {"JMP", "LOOP", "JCXZ"} | set(JCC)
MNEMONICS = ZERO_OPS | ONE_OP | TWO_OPS
