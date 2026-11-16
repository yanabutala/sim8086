"""sim8086 - a small 8086 assembler/simulator written in Python."""
from .assembler import assemble, AsmError
from .cpu import CPU, SimError

__all__ = ["assemble", "AsmError", "CPU", "SimError"]
__version__ = "1.0.0"
