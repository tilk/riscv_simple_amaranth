from amaranth import *


class PipelineExecControl(Elaboratable):
    def __init__(self):
        self.stall = Signal()
        self.insn_request = Signal()
        self.insn_kill = Signal()
        self.pc_we = Signal()
        self.step = Signal()

        self.insn_valid = Signal()
        self.mem_request = Signal()
        self.mem_valid = Signal()
        self.do_jump = Signal()
        self.want_stall = Signal()

    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.stall.eq(self.do_jump | self.want_stall)
        m.d.comb += self.insn_request.eq(~self.want_stall)
        m.d.comb += self.insn_kill.eq(self.do_jump)
        m.d.comb += self.step.eq((~self.insn_request | self.insn_valid) & (~self.mem_request | self.mem_valid))
        m.d.comb += self.pc_we.eq(self.step & (self.insn_request | self.do_jump))

        return m
