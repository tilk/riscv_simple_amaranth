from amaranth import *
from .. import isa
from ..constants import AluASel, AluBSel, WbSel, AluOp, PCSel
from ..arch import ArchVariant
from ..alu import Alu
from ..regfile import RegFile
from ..imm_gen import ImmGen
from ..insn_decoder import InsnDecoder
from .stage import Stage, WithPipeline


class PipelineDataPath(Elaboratable, WithPipeline):
    def __init__(self, variant: ArchVariant):
        self.variant = variant

        # Status signals
        self.opcode = Signal(isa.OPCODE_BITS)
        self.funct3 = Signal(3)
        self.funct7 = Signal(7)
        self.result_eqz = Signal()
        self.want_stall = Signal()
        self.ex_funct3 = Signal(3)

        # Control signals
        self.step = Signal()
        self.stall = Signal()
        self.insn_we = Signal()
        self.pc_we = Signal()
        self.reg_we = Signal()
        self.ctl_mem_stb = Signal()
        self.ctl_mem_we = Signal()
        self.insn_kill = Signal()
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSel)
        self.alu_op = Signal(AluOp)
        self.wb_sel = Signal(WbSel)
        self.pc_sel = Signal(PCSel)

        # Program memory
        self.pc = Signal(variant.BIT_WIDTH, init=0x400000)
        self.insn = Signal(isa.INSN_BITS)

        # Data memory
        self.mem_addr = Signal(variant.BIT_WIDTH)
        self.mem_rdata = Signal(variant.BIT_WIDTH)
        self.mem_wdata = Signal(variant.BIT_WIDTH)
        self.mem_funct3 = Signal(3)
        self.mem_stb = Signal()
        self.mem_we = Signal()

    def elaborate(self, platform):
        m = Module()

        m.submodules.insn_decoder = insn_decoder = InsnDecoder()
        m.submodules.alu = alu = Alu(self.variant)
        m.submodules.regfile = regfile = RegFile(self.variant)
        m.submodules.imm_gen = imm_gen = ImmGen(self.variant)

        next_pc = Signal.like(self.pc)
        pc_plus_4 = Signal.like(self.pc)
        pc_plus_imm = Signal.like(self.pc)
        insn = Signal.like(self.insn)

        m.d.comb += insn.eq(Mux(self.insn_kill, 0, self.insn))

        insn = self.pipeline_signal(m, Stage.IF, Stage.ID, insn)
        pc = self.pipeline_signal(m, Stage.IF, Stage.EX, self.pc)
        mem_rdata = self.pipeline_signal(m, Stage.MEM, Stage.WB, self.mem_rdata)
        reg_we = self.pipeline_signal(m, Stage.ID, Stage.WB, self.reg_we, bubble_value=0)
        alua_sel = self.pipeline_signal(m, Stage.ID, Stage.EX, self.alua_sel)
        alub_sel = self.pipeline_signal(m, Stage.ID, Stage.EX, self.alub_sel)
        alu_op = self.pipeline_signal(m, Stage.ID, Stage.EX, self.alu_op, bubble_value=AluOp.NONE)
        mem_stb = self.pipeline_signal(m, Stage.ID, Stage.MEM, self.ctl_mem_stb, bubble_value=0)
        mem_we = self.pipeline_signal(m, Stage.ID, Stage.MEM, self.ctl_mem_we, bubble_value=0)
        mem_funct3 = self.pipeline_signal(m, Stage.ID, Stage.MEM, self.funct3)
        wb_sel = self.pipeline_signal(m, Stage.ID, Stage.WB, self.wb_sel)
        rs1_data = self.pipeline_signal(m, Stage.ID, Stage.EX, regfile.rs1_data)
        rs2_data = self.pipeline_signal(m, Stage.ID, Stage.MEM, regfile.rs2_data)
        rd = self.pipeline_signal(m, Stage.ID, Stage.WB, insn_decoder.rd)
        imm = self.pipeline_signal(m, Stage.ID, Stage.WB, imm_gen.imm)
        alu_r = self.pipeline_signal(m, Stage.EX, Stage.WB, alu.r)

        m.d.comb += pc_plus_4.eq(pc[Stage.IF] + 4)
        m.d.comb += pc_plus_imm.eq(pc[Stage.EX] + imm[Stage.EX])

        pc_plus_4 = self.pipeline_signal(m, Stage.IF, Stage.WB, pc_plus_4)
        pc_plus_imm = self.pipeline_signal(m, Stage.EX, Stage.EX, pc_plus_imm)

        m.d.comb += imm_gen.insn.eq(insn[Stage.ID])
        m.d.comb += insn_decoder.insn.eq(insn[Stage.ID])
        m.d.comb += regfile.rs1_addr.eq(insn_decoder.rs1)
        m.d.comb += regfile.rs2_addr.eq(insn_decoder.rs2)
        m.d.comb += self.opcode.eq(insn_decoder.opcode)
        m.d.comb += self.funct3.eq(insn_decoder.funct3)
        m.d.comb += self.funct7.eq(insn_decoder.funct7)
        m.d.comb += self.result_eqz.eq(alu_r[Stage.EX] == 0)
        m.d.comb += self.ex_funct3.eq(mem_funct3[Stage.EX])
        m.d.comb += regfile.rd_addr.eq(rd[Stage.WB])
        m.d.comb += regfile.we.eq(reg_we[Stage.WB])
        m.d.comb += alu.alu_op.eq(alu_op[Stage.EX])
        m.d.comb += self.mem_stb.eq(mem_stb[Stage.MEM])
        m.d.comb += self.mem_we.eq(mem_we[Stage.MEM])
        m.d.comb += self.mem_addr.eq(alu_r[Stage.MEM])
        m.d.comb += self.mem_wdata.eq(rs2_data[Stage.MEM])
        m.d.comb += self.mem_funct3.eq(mem_funct3[Stage.MEM])

        with m.Switch(self.pc_sel):
            with m.Case(PCSel.PC4):
                m.d.comb += next_pc.eq(pc_plus_4[Stage.IF])
            with m.Case(PCSel.PC_IMM):
                m.d.comb += next_pc.eq(pc_plus_imm[Stage.EX])
            with m.Case(PCSel.RS1_IMM):
                m.d.comb += next_pc.eq(alu_r[Stage.EX])
            with m.Case(PCSel.PC4_BR):
                m.d.comb += next_pc.eq(pc_plus_4[Stage.EX])

        with m.If(self.pc_we):
            m.d.sync += self.pc.eq(next_pc)

        with m.Switch(alua_sel[Stage.EX]):
            with m.Case(AluASel.RS1):
                m.d.comb += alu.a.eq(rs1_data[Stage.EX])
            with m.Case(AluASel.PC):
                m.d.comb += alu.a.eq(pc[Stage.EX])

        with m.Switch(alub_sel[Stage.EX]):
            with m.Case(AluBSel.RS2):
                m.d.comb += alu.b.eq(rs2_data[Stage.EX])
            with m.Case(AluBSel.IMM):
                m.d.comb += alu.b.eq(imm[Stage.EX])

        with m.Switch(wb_sel[Stage.WB]):
            with m.Case(WbSel.ALU):
                m.d.comb += regfile.rd_data.eq(alu_r[Stage.WB])
            with m.Case(WbSel.IMM):
                m.d.comb += regfile.rd_data.eq(imm[Stage.WB])
            with m.Case(WbSel.PC4):
                m.d.comb += regfile.rd_data.eq(pc_plus_4[Stage.WB])
            with m.Case(WbSel.DATA):
                m.d.comb += regfile.rd_data.eq(mem_rdata[Stage.WB])

        want_stall = Cat(
            reg_we[s] & (alu_op[Stage.ID] != AluOp.NONE) & (rd[s] != 0) & (rd[s] == rs) & cond
            for s in [Stage.EX, Stage.MEM, Stage.WB]
            for (rs, cond) in [
                (insn_decoder.rs1, alua_sel[Stage.ID] == AluASel.RS1),
                (insn_decoder.rs2, alub_sel[Stage.ID] == AluBSel.RS2),
                (insn_decoder.rs2, mem_stb[Stage.ID] & mem_we[Stage.ID]),
            ]
        ).any()

        m.d.comb += self.want_stall.eq(want_stall)

        return m
