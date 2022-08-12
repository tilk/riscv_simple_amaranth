from amaranth import *
from ..constants import InsnSel


class SingleCycleBusControl(Elaboratable):
    def __init__(self):
        self.insn_valid = Signal()
        self.mem_ack = Signal()
        self.mem_stb = Signal()

        self.pc_we = Signal()

    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.pc_we.eq(self.mem_ack | self.insn_valid & ~self.mem_stb)

        return m
