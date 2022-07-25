from amaranth import *
from .arch import ArchVariant

class RegFile(Elaboratable):
    def __init__(self, variant: ArchVariant):
        self.variant = variant
        self.rs1_addr = Signal(variant.REGS_BITS)
        self.rs2_addr = Signal(variant.REGS_BITS)
        self.rd_addr  = Signal(variant.REGS_BITS)
        self.rs1_data = Signal(variant.BIT_WIDTH)
        self.rs2_data = Signal(variant.BIT_WIDTH)
        self.rd_data  = Signal(variant.BIT_WIDTH)
        self.we  = Signal()

    def elaborate(self, platform):
        m = Module()

        m.submodules.regs = regs = Memory(width=self.variant.BIT_WIDTH, depth=self.variant.REGS)
        m.submodules.ps1 = ps1 = regs.read_port(domain="comb")
        m.submodules.ps2 = ps2 = regs.read_port(domain="comb")
        m.submodules.pd  = pd  = regs.write_port()

        m.d.comb += ps1.addr.eq(self.rs1_addr)
        m.d.comb += self.rs1_data.eq(ps1.data)

        m.d.comb += ps2.addr.eq(self.rs2_addr)
        m.d.comb += self.rs2_data.eq(ps2.data)

        m.d.comb += pd.addr.eq(self.rd_addr)
        m.d.comb += pd.data.eq(self.rd_data)
        m.d.comb += pd.en.eq(self.we & self.rd_addr != 0)

        return m
