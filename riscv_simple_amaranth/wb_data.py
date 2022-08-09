from amaranth import *
from .arch import ArchVariant
from .isa import Funct3Mem


class WishboneData(Elaboratable):
    def __init__(self, variant: ArchVariant):
        self.variant = variant

        self.mem_addr = Signal(variant.BIT_WIDTH)
        self.mem_rdata = Signal(variant.BIT_WIDTH)
        self.mem_wdata = Signal(variant.BIT_WIDTH)
        self.mem_funct3 = Signal(Funct3Mem)

        self.wb_adr_o = Signal(variant.BIT_WIDTH - variant.BYTE_WIDTH_BITS)
        self.wb_dat_i = Signal(variant.BIT_WIDTH)
        self.wb_dat_o = Signal(variant.BIT_WIDTH)
        self.wb_sel_o = Signal(variant.BYTE_WIDTH)

    def elaborate(self, platform):
        m = Module()

        sel_mask = Signal(self.variant.BYTE_WIDTH)
        byte_off = self.mem_addr[0 : self.variant.BYTE_WIDTH_BITS]
        bit_off = byte_off << 3
        rdata_shifted = self.wb_dat_i >> bit_off

        m.d.comb += self.wb_adr_o.eq(self.mem_addr >> self.variant.BYTE_WIDTH_BITS)
        m.d.comb += self.wb_sel_o.eq(sel_mask << byte_off)
        m.d.comb += self.wb_dat_o.eq(self.mem_wdata << bit_off)

        with m.Switch(self.mem_funct3[0:2]):
            for i in range(self.variant.BYTE_WIDTH_BITS + 1):
                with m.Case(i):
                    m.d.comb += sel_mask.eq(2 ** (2**i) - 1)
                    bit_width = 8 * (2**i)
                    sign_bit = rdata_shifted[bit_width - 1] & ~self.mem_funct3[2]
                    m.d.comb += self.mem_rdata.eq(
                        Cat(rdata_shifted[0:bit_width], Repl(sign_bit, self.variant.BIT_WIDTH - bit_width))
                    )

        return m
