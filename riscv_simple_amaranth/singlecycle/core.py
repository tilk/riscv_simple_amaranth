from amaranth import *
from ..arch import ArchVariant
from .. import isa
from .ctlpath import SingleCycleControlPath
from .datapath import SingleCycleDataPath
from ..busbuffer import BusBuffer
from ..wb_data import WishboneData


class SingleCycleCore(Elaboratable):
    def __init__(self, variant: ArchVariant):
        self.variant = variant

        self.mem_adr_o = Signal(variant.BIT_WIDTH - variant.BYTE_WIDTH_BITS)
        self.mem_dat_i = Signal(variant.BIT_WIDTH)
        self.mem_dat_o = Signal(variant.BIT_WIDTH)
        self.mem_we_o = Signal()
        self.mem_sel_o = Signal(variant.BYTE_WIDTH)
        self.mem_stb_o = Signal()
        self.mem_cyc_o = Signal()
        self.mem_ack_i = Signal()

        self.insn_adr_o = Signal(variant.BIT_WIDTH - 2)
        self.insn_dat_i = Signal(isa.INSN_BITS)
        self.insn_stb_o = Signal()
        self.insn_cyc_o = Signal()
        self.insn_ack_i = Signal()

    def elaborate(self, platform):
        m = Module()

        m.submodules.ctl = ctl = SingleCycleControlPath()
        m.submodules.data = data = SingleCycleDataPath(self.variant)
        m.submodules.data_iface = data_iface = WishboneData(self.variant)
        m.submodules.bbinsn = bbinsn = BusBuffer(isa.INSN_BITS)

        m.d.comb += ctl.opcode.eq(data.opcode)
        m.d.comb += ctl.funct3.eq(data.funct3)
        m.d.comb += ctl.funct7.eq(data.funct7)
        m.d.comb += ctl.result_eqz.eq(data.result_eqz)
        m.d.comb += ctl.insn_valid.eq(bbinsn.valid)
        m.d.comb += ctl.mem_ack.eq(self.mem_ack_i)
        m.d.comb += data.insn.eq(bbinsn.data_buf)
        m.d.comb += data.pc_we.eq(ctl.pc_we)
        m.d.comb += data.reg_we.eq(ctl.reg_we)
        m.d.comb += data.alua_sel.eq(ctl.alua_sel)
        m.d.comb += data.alub_sel.eq(ctl.alub_sel)
        m.d.comb += data.alu_op.eq(ctl.alu_op)
        m.d.comb += data.wb_sel.eq(ctl.wb_sel)
        m.d.comb += data.pc_sel.eq(ctl.pc_sel)

        m.d.comb += data_iface.mem_addr.eq(data.mem_addr)
        m.d.comb += data_iface.mem_wdata.eq(data.mem_wdata)
        m.d.comb += data_iface.mem_funct3.eq(data.funct3)
        m.d.comb += data.mem_rdata.eq(data_iface.mem_rdata)

        m.d.comb += self.mem_adr_o.eq(data_iface.wb_adr_o)
        m.d.comb += self.mem_dat_o.eq(data_iface.wb_dat_o)
        m.d.comb += self.mem_we_o.eq(ctl.mem_we)
        m.d.comb += self.mem_sel_o.eq(data_iface.wb_sel_o)
        m.d.comb += self.mem_stb_o.eq(ctl.mem_stb)
        m.d.comb += self.mem_cyc_o.eq(ctl.mem_stb)
        m.d.comb += data_iface.wb_dat_i.eq(self.mem_dat_i)

        m.d.comb += bbinsn.data.eq(self.insn_dat_i)
        m.d.comb += bbinsn.reset.eq(ctl.pc_we)
        m.d.comb += bbinsn.request.eq(1)
        m.d.comb += bbinsn.ack.eq(self.insn_ack_i)
        m.d.comb += self.insn_adr_o.eq(data.pc[2 : self.variant.BIT_WIDTH])
        m.d.comb += self.insn_stb_o.eq(bbinsn.stb)
        m.d.comb += self.insn_cyc_o.eq(bbinsn.stb)

        return m
