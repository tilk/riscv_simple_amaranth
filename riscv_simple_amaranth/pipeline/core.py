from amaranth import *
from ..arch import ArchVariant
from .. import isa
from .ctlpath import PipelineControlPath
from .datapath import PipelineDataPath
from ..busbuffer import BusBuffer
from ..wb_data import WishboneData


class PipelineCore(Elaboratable):
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

        m.submodules.ctl = ctl = PipelineControlPath()
        m.submodules.data = data = PipelineDataPath(self.variant)
        m.submodules.data_iface = data_iface = WishboneData(self.variant)
        m.submodules.bbinsn = bbinsn = BusBuffer(isa.INSN_BITS)
        m.submodules.bbdata = bbdata = BusBuffer(self.variant.BIT_WIDTH)

        m.d.comb += ctl.opcode.eq(data.opcode)
        m.d.comb += ctl.funct3.eq(data.funct3)
        m.d.comb += ctl.funct7.eq(data.funct7)
        m.d.comb += ctl.result_eqz.eq(data.result_eqz)
        m.d.comb += ctl.want_stall.eq(data.want_stall)
        m.d.comb += ctl.insn_valid.eq(bbinsn.valid)
        m.d.comb += ctl.mem_valid.eq(bbdata.valid)
        m.d.comb += ctl.mem_request.eq(data.mem_stb)
        m.d.comb += data.insn.eq(self.insn_dat_i)
        m.d.comb += data.insn_we.eq(ctl.insn_we)
        m.d.comb += data.pc_we.eq(ctl.pc_we)
        m.d.comb += data.reg_we.eq(ctl.reg_we)
        m.d.comb += data.alua_sel.eq(ctl.alua_sel)
        m.d.comb += data.alub_sel.eq(ctl.alub_sel)
        m.d.comb += data.alu_op.eq(ctl.alu_op)
        m.d.comb += data.wb_sel.eq(ctl.wb_sel)
        m.d.comb += data.pc_sel.eq(ctl.pc_sel)
        m.d.comb += data.ctl_mem_stb.eq(ctl.mem_stb)
        m.d.comb += data.ctl_mem_we.eq(ctl.mem_we)
        m.d.comb += data.step.eq(ctl.step)
        m.d.comb += data.stall.eq(ctl.stall)

        m.d.comb += data_iface.mem_addr.eq(data.mem_addr)
        m.d.comb += data_iface.mem_wdata.eq(data.mem_wdata)
        m.d.comb += data_iface.mem_funct3.eq(data.mem_funct3)
        m.d.comb += data.mem_rdata.eq(data_iface.mem_rdata)

        m.d.comb += self.mem_adr_o.eq(data_iface.wb_adr_o)
        m.d.comb += self.mem_dat_o.eq(data_iface.wb_dat_o)
        m.d.comb += self.mem_we_o.eq(data.mem_we)
        m.d.comb += self.mem_sel_o.eq(data_iface.wb_sel_o)
        m.d.comb += self.mem_stb_o.eq(bbdata.stb)
        m.d.comb += self.mem_cyc_o.eq(bbdata.stb)
        m.d.comb += data_iface.wb_dat_i.eq(self.mem_dat_i)

        m.d.comb += bbinsn.data.eq(self.insn_dat_i)
        m.d.comb += bbinsn.reset.eq(ctl.step)
        m.d.comb += bbinsn.request.eq(ctl.insn_request)
        m.d.comb += bbinsn.ack.eq(self.insn_ack_i)
        m.d.comb += self.insn_adr_o.eq(data.pc[2 : self.variant.BIT_WIDTH])
        m.d.comb += self.insn_stb_o.eq(bbinsn.stb)
        m.d.comb += self.insn_cyc_o.eq(bbinsn.stb)

        m.d.comb += bbdata.data.eq(self.mem_dat_i)
        m.d.comb += bbdata.reset.eq(ctl.step)
        m.d.comb += bbdata.request.eq(data.mem_stb)
        m.d.comb += bbdata.ack.eq(self.mem_ack_i)
        m.d.comb += self.mem_stb_o.eq(bbdata.stb)
        m.d.comb += self.mem_cyc_o.eq(bbdata.stb)

        return m
