from amaranth import *

class RegFile(Elaboratable):
    def __init__(self, variant):
        self.variant = variant
        self.as1 = Signal(variant.REGS_BITS)
        self.as2 = Signal(variant.REGS_BITS)
        self.ad  = Signal(variant.REGS_BITS)
        self.rs1 = Signal(variant.BIT_WIDTH)
        self.rs2 = Signal(variant.BIT_WIDTH)
        self.rd  = Signal(variant.BIT_WIDTH)
        self.we  = Signal()

    def elaborate(self, platform):
        m = Module()

        m.submodules.regs = regs = Memory(width=self.variant.BIT_WIDTH, depth=self.variant.REGS)
        m.submodules.ps1 = ps1 = regs.read_port(domain="comb")
        m.submodules.ps2 = ps2 = regs.read_port(domain="comb")
        m.submodules.pd  = pd  = regs.write_port()

        m.d.comb += ps1.addr.eq(self.as1)
        m.d.comb += self.rs1.eq(ps1.data)

        m.d.comb += ps2.addr.eq(self.as2)
        m.d.comb += self.rs2.eq(ps2.data)

        m.d.comb += pd.addr.eq(self.ad)
        m.d.comb += pd.data.eq(self.rd)
        m.d.comb += pd.en.eq(self.we & self.ad != 0)

        return m
