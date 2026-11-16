import os
import unittest

from sim8086 import assemble, CPU, AsmError, SimError

HERE = os.path.dirname(__file__)
EX = os.path.join(HERE, "..", "examples")


def run(src):
    cpu = CPU(assemble(src))
    cpu.run()
    return cpu


def words(cpu, start, n):
    return [cpu.mem_read(start + 2 * i, 16) for i in range(n)]


class ExampleTests(unittest.TestCase):
    def test_bubble_sort(self):
        with open(os.path.join(EX, "bubble_sort.asm")) as f:
            cpu = run(f.read())
        self.assertEqual(words(cpu, 0x500, 20),
                         [3, 9, 15, 18, 77, 123, 250, 256, 500, 872, 999, 1500, 2048,
                          4500, 12345, 31000, 32768, 40000, 60000, 65000])

    def test_fibonacci(self):
        with open(os.path.join(EX, "fibonacci.asm")) as f:
            cpu = run(f.read())
        self.assertEqual(words(cpu, 0x500, 15),
                         [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377])
        self.assertEqual((cpu.regs["AX"], cpu.regs["BX"], cpu.regs["SI"]), (0x262, 0x3DB, 0x51E))


class InstructionTests(unittest.TestCase):
    def test_mov_add_flags(self):
        cpu = run("MOV AX, 0FFFFh\nADD AX, 1\nHLT")
        self.assertEqual(cpu.regs["AX"], 0)
        self.assertEqual((cpu.flags["CF"], cpu.flags["ZF"]), (1, 1))

    def test_8bit_registers(self):
        cpu = run("MOV AX, 0\nMOV AH, 12h\nMOV AL, 34h")
        self.assertEqual(cpu.regs["AX"], 0x1234)

    def test_memory_little_endian(self):
        cpu = run("MOV word [1280], 4500")
        self.assertEqual(cpu.mem[0x500:0x502], bytes([0x94, 0x11]))

    def test_unsigned_vs_signed_jump(self):
        # 40000 is bigger than 4500 when unsigned, but negative (smaller) when signed
        unsigned = run("MOV AX, 40000\nMOV BX, 4500\nCMP AX, BX\nJBE small\nMOV CX, 1\nHLT\nsmall: MOV CX, 2")
        signed = run("MOV AX, 40000\nMOV BX, 4500\nCMP AX, BX\nJLE small\nMOV CX, 1\nHLT\nsmall: MOV CX, 2")
        self.assertEqual(unsigned.regs["CX"], 1)
        self.assertEqual(signed.regs["CX"], 2)

    def test_loop_and_stack(self):
        cpu = run("MOV CX, 5\nMOV AX, 0\nagain: ADD AX, CX\nLOOP again\nPUSH AX\nPOP BX")
        self.assertEqual((cpu.regs["AX"], cpu.regs["BX"]), (15, 15))

    def test_mul_div(self):
        cpu = run("MOV AX, 300\nMOV BX, 200\nMUL BX\nMOV CX, 7\nDIV CX")
        self.assertEqual((cpu.regs["AX"], cpu.regs["DX"]), (60000 // 7, 60000 % 7))

    def test_inc_keeps_carry(self):
        cpu = run("MOV AX, 0FFFFh\nADD AX, 1\nINC BX")
        self.assertEqual(cpu.flags["CF"], 1)


class ErrorTests(unittest.TestCase):
    def test_unknown_instruction(self):
        with self.assertRaises(AsmError):
            assemble("FOO AX, 1")

    def test_missing_label(self):
        with self.assertRaises(AsmError):
            assemble("JMP nowhere")

    def test_wrong_operand_count(self):
        with self.assertRaises(AsmError):
            assemble("MOV AX")

    def test_size_needed(self):
        with self.assertRaises(SimError):
            run("MOV [SI], 5")

    def test_endless_loop_is_stopped(self):
        cpu = CPU(assemble("here: JMP here"))
        with self.assertRaises(SimError):
            cpu.run(max_steps=1000)


if __name__ == "__main__":
    unittest.main()
