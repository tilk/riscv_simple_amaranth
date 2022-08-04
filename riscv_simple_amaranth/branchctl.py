from amaranth import *
from .isa import Funct3Branch


class BranchControl(Elaboratable):
    def __init__(self):
        self.result_eqz = Signal()
        self.funct3 = Signal(3)
        self.take_branch = Signal()

    def elaborate(self, platform):
        m = Module()

        with m.Switch(self.funct3):
            with m.Case(Funct3Branch.EQ):
                m.d.comb += self.take_branch.eq(~self.result_eqz)
            with m.Case(Funct3Branch.NE):
                m.d.comb += self.take_branch.eq(self.result_eqz)
            with m.Case(Funct3Branch.LT):
                m.d.comb += self.take_branch.eq(~self.result_eqz)
            with m.Case(Funct3Branch.GE):
                m.d.comb += self.take_branch.eq(self.result_eqz)
            with m.Case(Funct3Branch.LTU):
                m.d.comb += self.take_branch.eq(~self.result_eqz)
            with m.Case(Funct3Branch.GEU):
                m.d.comb += self.take_branch.eq(self.result_eqz)

        return m
