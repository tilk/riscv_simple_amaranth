from amaranth import *
from .arch import ArchVariant
from . import isa


class WishboneInsn(Elaboratable):
    def __init__(self, variant: ArchVariant):
        self.variant = variant

        self.pc = Signal(variant.BIT_WIDTH)
        self.insn = Signal(isa.INSN_BITS)
        self.insn_req = Signal()
        self.insn_ack = Signal()

        self.wb_adr_o = Signal(variant.BIT_WIDTH - 2)
        self.wb_dat_i = Signal(isa.INSN_BITS)
        self.wb_stb_o = Signal()
        self.wb_cyc_o = Signal()
        self.wb_ack_i = Signal()

    def elaborate(self, platform):
        m = Module()

        insn_reg = Signal.like(self.insn)

        return m
