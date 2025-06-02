from amaranth import *
from amaranth.tracer import get_var_name
from enum import IntEnum


class Stage(IntEnum):
    IF = 0
    ID = 1
    EX = 2
    MEM = 3
    WB = 4


class WithPipeline:
    stall: Signal
    insn_kill: Signal
    step: Signal

    def pipeline_signal(self, m: Module, start: Stage, end: Stage, init, *, bubble_value=None) -> dict[Stage, Signal]:
        name = get_var_name()
        d: dict[Stage, Signal] = {}
        for s in range(start, end + 1):
            d[Stage(s)] = Signal.like(init, name=name + str(Stage(s)))
        m.d.comb += d[start].eq(init)
        with m.If(self.step):
            for s in range(start, end):
                m.d.sync += d[Stage(s + 1)].eq(d[Stage(s)])
            if bubble_value is not None:
                if Stage.EX in d:
                    with m.If(self.stall):
                        m.d.sync += d[Stage.EX].eq(bubble_value)
            if start == Stage.IF:
                with m.If(self.stall & ~self.insn_kill):
                    m.d.sync += d[Stage.ID].eq(d[Stage.ID])
        return d
