from amaranth import *
from . import isa

class InsnDecoder(Elaboratable):
    def __init__(self):
        self.insn   = Signal(isa.INSN_BITS)
        self.opcode = Signal(isa.OPCODE_BITS)
        self.funct3 = Signal(3)
        self.funct7 = Signal(7)
        self.rd     = Signal(isa.REGS_BITS)
        self.rs1    = Signal(isa.REGS_BITS)
        self.rs2    = Signal(isa.REGS_BITS)

    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.opcode.eq(self.insn[0:7])
        m.d.comb += self.funct3.eq(self.insn[12:15])
        m.d.comb += self.funct7.eq(self.insn[25:32])
        m.d.comb += self.rd.eq(self.insn[7:12])
        m.d.comb += self.rs1.eq(self.insn[15:20])
        m.d.comb += self.rs2.eq(self.insn[20:25])

        return m
