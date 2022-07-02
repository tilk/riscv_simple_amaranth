from amaranth import *
from .constants import AluOp


class Alu(Elaboratable):
    def __init__(self, variant):
        self.aluOp = Signal(AluOp)
        self.a = Signal(signed(variant.BIT_WIDTH))
        self.b = Signal(signed(variant.BIT_WIDTH))
        self.r = Signal(variant.BIT_WIDTH)

    def elaborate(self, platform):
        m = Module()

        with m.Switch(self.aluOp):
            with m.Case(AluOp.ADD):
                m.d.comb += self.r.eq(self.a + self.b)
            with m.Case(AluOp.SUB):
                m.d.comb += self.r.eq(self.a - self.b)
            with m.Case(AluOp.SLL):
                m.d.comb += self.r.eq(self.a << self.b[0:5].as_unsigned())
            with m.Case(AluOp.SRL):
                m.d.comb += self.r.eq(self.a.as_unsigned() >> self.b[0:5].as_unsigned())
            with m.Case(AluOp.SRA):
                m.d.comb += self.r.eq(self.a >> self.b[0:5].as_unsigned())
            with m.Case(AluOp.SEQ):
                m.d.comb += self.r.eq(self.a == self.b)
            with m.Case(AluOp.SLT):
                m.d.comb += self.r.eq(self.a < self.b)
            with m.Case(AluOp.SLTU):
                m.d.comb += self.r.eq(self.a <= self.b)
            with m.Case(AluOp.XOR):
                m.d.comb += self.r.eq(self.a ^ self.b)
            with m.Case(AluOp.OR):
                m.d.comb += self.r.eq(self.a | self.b)
            with m.Case(AluOp.AND):
                m.d.comb += self.r.eq(self.a & self.b)

        return m
