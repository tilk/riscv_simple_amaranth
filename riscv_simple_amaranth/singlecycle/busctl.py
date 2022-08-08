from amaranth import *
from ..constants import InsnSel


class SingleCycleBusControl(Elaboratable):
    def __init__(self):
        self.insn_ack = Signal()
        self.mem_ack = Signal()
        self.mem_stb = Signal()

        self.insn_we = Signal()
        self.pc_we = Signal()
        self.insn_sel = Signal(InsnSel)
        self.insn_stb = Signal()

    def elaborate(self, platform):
        m = Module()

        has_stored_inst = Signal()

        m.d.comb += self.pc_we.eq(self.mem_ack | self.insn_ack & ~self.mem_stb)
        m.d.comb += self.insn_stb.eq(~has_stored_inst)

        with m.If(has_stored_inst):
            m.d.comb += self.insn_sel.eq(InsnSel.IR)

        with m.If(self.insn_ack):
            m.d.comb += self.insn_we.eq(1)
            m.d.comb += self.insn_sel.eq(InsnSel.INSN)
            m.d.sync += has_stored_inst.eq(1)

        with m.If(self.pc_we):
            m.d.sync += has_stored_inst.eq(0)

        return m
