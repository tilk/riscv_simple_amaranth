from amaranth import *
from . import isa
from .arch import ArchVariant

class ImmGen(Elaboratable):
    def __init__(self, variant: ArchVariant):
        self.insn = Signal(isa.INSN_BITS)
        self.imm = Signal(variant.BIT_WIDTH)

    def elaborate(self, platform):
        m = Module()

        insn = self.insn

        with m.Switch(insn[0:7]):
            with m.Case(isa.Opcode.LOAD, isa.Opcode.OP_IMM, isa.Opcode.JALR):
                m.d.comb += self.imm.eq(Cat(insn[20], insn[21:25], insn[25:31], insn[31]).as_signed())
            with m.Case(isa.Opcode.STORE):
                m.d.comb += self.imm.eq(Cat(insn[7], insn[8:12], insn[25:31], insn[31]).as_signed())
            with m.Case(isa.Opcode.BRANCH):
                m.d.comb += self.imm.eq(Cat(C(0, 1), insn[8:12], insn[25:31], insn[7], insn[31]).as_signed())
            with m.Case(isa.Opcode.AUIPC, isa.Opcode.LUI):
                m.d.comb += self.imm.eq(Cat(C(0, 12), insn[12:20], insn[20:32]).as_signed())
            with m.Case(isa.Opcode.JAL):
                m.d.comb += self.imm.eq(Cat(C(0, 1), insn[21:25], insn[25:31], insn[20], insn[12:20], insn[31]).as_signed())

        return m
