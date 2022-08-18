from amaranth import *
from .. import isa
from ..constants import AluASel, AluBSel, WbSel, AluOp, PCSel, InsnSel
from ..arch import ArchVariant
from ..alu import Alu
from ..regfile import RegFile
from ..imm_gen import ImmGen
from ..insn_decoder import InsnDecoder
from .stage import Stage


class PipelineDataPath(Elaboratable):
    def __init__(self, variant: ArchVariant):
        self.variant = variant

        # Status signals
        self.opcode = Signal(isa.OPCODE_BITS)
        self.funct3 = Signal(3)
        self.funct7 = Signal(7)
        self.result_eqz = Signal()
        self.want_stall = Signal()

        # Control signals
        self.step = Signal()
        self.stall = Signal()
        self.insn_we = Signal()
        self.pc_we = Signal()
        self.reg_we = Signal()
        self.ctl_mem_stb = Signal()
        self.ctl_mem_we = Signal()
        self.insn_sel = Signal(InsnSel)
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSel)
        self.alu_op = Signal(AluOp)
        self.wb_sel = Signal(WbSel)
        self.pc_sel = Signal(PCSel)

        # Program memory
        self.pc = Signal(variant.BIT_WIDTH, reset=0x400000)
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

        def pipeline_signal(start: Stage, end: Stage, init, shape = None, *, name = None, bubble_value = None) -> dict[Stage, Signal]:
            if shape is None:
                shape = init.shape()
            if name is None:
                name = init.name
            d: dict[Stage, Signal] = {}
            for s in range(start, end + 1):
                d[Stage(s)] = Signal(shape, name = name + str(Stage(s)))
            m.d.comb += d[start].eq(init)
            for s in range(start, end):
                with m.If(self.step):
                    m.d.sync += d[Stage(s+1)].eq(d[Stage(s)])
            if bubble_value is not None:
                if Stage.EX in d:
                    with m.If(self.stall & self.step):
                        m.d.sync += d[Stage.EX].eq(bubble_value)
            return d
        
        insn = pipeline_signal(Stage.IF, Stage.ID, self.insn)
        pc = pipeline_signal(Stage.IF, Stage.EX, self.pc)
        mem_rdata = pipeline_signal(Stage.MEM, Stage.WB, self.mem_rdata)
        reg_we = pipeline_signal(Stage.ID, Stage.WB, self.reg_we, bubble_value = 0)
        alua_sel = pipeline_signal(Stage.ID, Stage.EX, self.alua_sel)
        alub_sel = pipeline_signal(Stage.ID, Stage.EX, self.alub_sel)
        alu_op = pipeline_signal(Stage.ID, Stage.EX, self.alu_op, bubble_value = AluOp.NONE)
        mem_stb = pipeline_signal(Stage.ID, Stage.MEM, self.ctl_mem_stb, bubble_value = 0)
        mem_we = pipeline_signal(Stage.ID, Stage.MEM, self.ctl_mem_we, bubble_value = 0)
        mem_funct3 = pipeline_signal(Stage.ID, Stage.MEM, self.funct3)
        wb_sel = pipeline_signal(Stage.ID, Stage.WB, self.wb_sel)
        rs1_data = pipeline_signal(Stage.ID, Stage.EX, regfile.rs1_data)
        rs2_data = pipeline_signal(Stage.ID, Stage.MEM, regfile.rs2_data)
        rd = pipeline_signal(Stage.ID, Stage.WB, insn_decoder.rd)
        imm = pipeline_signal(Stage.ID, Stage.WB, imm_gen.imm)
        pc_plus_4 = pipeline_signal(Stage.IF, Stage.WB, pc[Stage.IF] + 4, self.pc.shape(), name = "pc_plus_4")
        pc_plus_imm = pipeline_signal(Stage.EX, Stage.EX, pc[Stage.EX] + imm[Stage.EX], self.pc.shape(), name = "pc_plus_imm")
        alu_r = pipeline_signal(Stage.EX, Stage.WB, alu.r)

        m.d.comb += imm_gen.insn.eq(insn[Stage.ID])
        m.d.comb += insn_decoder.insn.eq(insn[Stage.ID])
        m.d.comb += regfile.rs1_addr.eq(insn_decoder.rs1)
        m.d.comb += regfile.rs2_addr.eq(insn_decoder.rs2)
        m.d.comb += self.opcode.eq(insn_decoder.opcode)
        m.d.comb += self.funct3.eq(insn_decoder.funct3)
        m.d.comb += self.funct7.eq(insn_decoder.funct7)
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

        want_stall = Cat(reg_we[s] & (alu_op[Stage.ID] != AluOp.NONE) & (rd[s] != 0) & (rd[s] == rs) & cond
                for s in [Stage.EX, Stage.MEM, Stage.WB]
                for (rs, cond) in [(insn_decoder.rs1, alua_sel[Stage.ID] == AluASel.RS1),
                                   (insn_decoder.rs2, alub_sel[Stage.ID] == AluBSel.RS2),
                                   (insn_decoder.rs2, mem_stb[Stage.ID] & mem_we[Stage.ID])])

        m.d.comb += self.want_stall.eq(want_stall)

        return m
