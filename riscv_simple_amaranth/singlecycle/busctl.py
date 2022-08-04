from amaranth import *


class SingleCycleBusControl(Elaboratable):
    def __init__(self):
        self.insn_ack = Signal()
        self.mem_ack = Signal()
        self.mem_re = Signal()
        self.mem_we = Signal()

        self.insn_we = Signal()
        self.pc_we = Signal()

    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.insn_we.eq(self.insn_ack)
        m.d.comb += self.pc_we.eq(self.mem_ack | ~(self.mem_re | self.mem_we))

        return m
