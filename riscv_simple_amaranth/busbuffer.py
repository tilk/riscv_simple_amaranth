from amaranth import *


class BusBuffer(Elaboratable):
    def __init__(self, width):
        self.data = Signal(width)
        self.reset = Signal()
        self.request = Signal()
        self.ack = Signal()

        self.data_buf = Signal(width)
        self.valid = Signal(width)
        self.stb = Signal()

    def elaborate(self, platform):
        m = Module()

        buf = Signal.like(self.data)
        has_buf = Signal()

        with m.If(has_buf):
            m.d.comb += self.valid.eq(1)
            m.d.comb += self.data_buf.eq(buf)

        with m.If(self.ack):
            m.d.sync += buf.eq(self.data)
            m.d.sync += has_buf.eq(1)
            m.d.comb += self.valid.eq(1)
            m.d.comb += self.data_buf.eq(self.data)

        with m.If(self.reset):
            m.d.sync += buf.eq(0)
            m.d.sync += has_buf.eq(0)

        m.d.comb += self.stb.eq(self.request & ~has_buf)

        return m
