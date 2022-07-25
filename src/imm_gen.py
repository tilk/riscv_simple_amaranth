from amaranth import *
from . import isa
from .arch import ArchVariant

class ImmGen(Elaboratable):
    def __init__(self, variant: ArchVariant):
        self.inst = Signal(isa.INSN_BITS)
        self.imm = Signal(variant.BIT_WIDTH)

    def elaborate(self, platform):
        m = Module()

        inst = self.inst

        with m.Switch(inst[0:7]):
            with m.Case(isa.Opcode.LOAD, isa.Opcode.OP_IMM, isa.Opcode.JALR):
                m.d.comb += self.imm.eq(Cat(inst[20], inst[21:25], inst[25:31], inst[31]).as_signed())
            with m.Case(isa.Opcode.STORE):
                m.d.comb += self.imm.eq(Cat(inst[7], inst[8:12], inst[25:31], inst[31]).as_signed())
            with m.Case(isa.Opcode.BRANCH):
                m.d.comb += self.imm.eq(Cat(C(0, 1), inst[8:12], inst[25:31], inst[7], inst[31]).as_signed())
            with m.Case(isa.Opcode.AUIPC, isa.Opcode.LUI):
                m.d.comb += self.imm.eq(Cat(C(0, 12), inst[12:20], inst[20:32]).as_signed())
            with m.Case(isa.Opcode.JAL):
                m.d.comb += self.imm.eq(Cat(C(0, 1), inst[21:25], inst[25:31], inst[20], inst[12:20], inst[31]).as_signed())

        return m
