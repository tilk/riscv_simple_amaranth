from amaranth import *
from amaranth.lib.enum import IntEnum

__all__ = ["INSN_BITS", "OPCODE_BITS", "REGS_BITS", "Funct3Alu", "Funct3Mem", "Funct3Branch", "Opcode"]

INSN_BITS = 32
OPCODE_BITS = 7
REGS_BITS = 5


class Funct3Alu(IntEnum, shape=3):
    ADD = 0b000
    SLL = 0b001
    SLT = 0b010
    SLTU = 0b011
    XOR = 0b100
    SRL = 0b101
    OR = 0b110
    AND = 0b111


class Funct3Mem(IntEnum, shape=3):
    BYTE = 0b000
    HALF = 0b001
    WORD = 0b010
    BYTE_U = 0b100
    HALF_U = 0b101


class Funct3Branch(IntEnum, shape=3):
    EQ = 0b000
    NE = 0b001
    LT = 0b100
    GE = 0b101
    LTU = 0b110
    GEU = 0b111


class Opcode(IntEnum, shape=7):
    ILLEGAL = 0b0000000
    LOAD = 0b0000011
    OP_IMM = 0b0010011
    AUIPC = 0b0010111
    STORE = 0b0100011
    OP = 0b0110011
    LUI = 0b0110111
    BRANCH = 0b1100011
    JALR = 0b1100111
    JAL = 0b1101111
