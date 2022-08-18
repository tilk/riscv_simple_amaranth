from enum import Enum


class AluOp(Enum):
    NONE = 0
    ADD = 1
    SUB = 2
    SLL = 3
    SRL = 4
    SRA = 5
    SEQ = 6
    SLT = 7
    SLTU = 8
    XOR = 9
    OR = 10
    AND = 11


class AluOpType(Enum):
    ADD = 0
    BRANCH = 1
    OP = 2
    OP_IMM = 3


class WbSel(Enum):
    ALU = 0
    DATA = 1
    PC4 = 2
    IMM = 3


class AluASel(Enum):
    RS1 = 0
    PC = 1


class AluBSel(Enum):
    RS2 = 0
    IMM = 1


class PCSel(Enum):
    PC4 = 0
    PC_IMM = 1
    RS1_IMM = 2
    PC4_BR = 3


class InsnSel(Enum):
    ZERO = 0
    INSN = 1
    IR = 2


class AddrSel(Enum):
    PC = 0
    ALU_REG = 1


class WbSelMC(Enum):
    ALU_REG = 0
    DATA = 1
    PC = 2
    IMM = 3


class PCSelMC(Enum):
    ALU = 0
    ALU_REG = 1


class AluBSelMC(Enum):
    RS2 = 0
    IMM = 1
    FOUR = 2
