from amaranth import *
from .. import isa
from ..constants import AluASel, AluBSel, WbSel, AluOp, PCSel, InsnSel
from ..arch import ArchVariant
from ..alu import Alu
from ..regfile import RegFile
from ..imm_gen import ImmGen
from ..insn_decoder import InsnDecoder

class SingleCycleDataPath(Elaboratable):
    def __init__(self, variant: ArchVariant):
        self.variant = variant

        # Status signals
        self.opcode = Signal(isa.OPCODE_BITS)
        self.funct3 = Signal(3)
        self.funct7 = Signal(7)
        self.result_eqz = Signal()
        
        # Control signals
        self.insn_we = Signal()
        self.pc_we = Signal()
        self.reg_we = Signal()
        self.insn_sel = Signal(InsnSel)
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSel)
        self.alu_op = Signal(AluOp)
        self.wb_sel = Signal(WbSel)
        self.pc_sel = Signal(PCSel)

        # Program memory
        self.pc = Signal(variant.BIT_WIDTH)
        self.insn = Signal(isa.INSN_BITS)

        # Data memory
        self.mem_addr = Signal(variant.BIT_WIDTH)
        self.mem_rdata = Signal(variant.BIT_WIDTH)
        self.mem_wdata = Signal(variant.BIT_WIDTH)

    def elaborate(self, platform):
        m = Module()

        m.submodules.insn_decoder = insn_decoder = InsnDecoder()
        m.submodules.alu = alu = Alu(self.variant)
        m.submodules.regfile = regfile = RegFile(self.variant)
        m.submodules.imm_gen = imm_gen = ImmGen(self.variant)

        insn_reg = Signal.like(self.insn)
        insn = Signal.like(self.insn)

        with m.Switch(self.insn_sel):
            with m.Case(InsnSel.INSN):
                m.d.comb += insn.eq(self.insn)
            with m.Case(InsnSel.IR):
                m.d.comb += insn.eq(insn_reg)

        with m.If(self.insn_we):
            m.d.sync += insn_reg.eq(self.insn)

        m.d.comb += insn_decoder.insn.eq(insn)
        m.d.comb += imm_gen.insn.eq(insn)
        m.d.comb += self.opcode.eq(insn_decoder.opcode)
        m.d.comb += self.funct3.eq(insn_decoder.funct3)
        m.d.comb += self.funct7.eq(insn_decoder.funct7)
        m.d.comb += self.result_eqz.eq(alu.r == 0)
        m.d.comb += alu.alu_op.eq(self.alu_op)
        m.d.comb += regfile.rs1_addr.eq(insn_decoder.rs1)
        m.d.comb += regfile.rs2_addr.eq(insn_decoder.rs2)
        m.d.comb += regfile.rd_addr.eq(insn_decoder.rd)
        m.d.comb += regfile.we.eq(self.reg_we)
        m.d.comb += self.mem_wdata.eq(regfile.rs2_data)
        m.d.comb += self.mem_addr.eq(alu.r)

        next_pc = Signal.like(self.pc)
        pc_plus_4 = self.pc + 4
        pc_plus_imm = self.pc + imm_gen.imm

        with m.Switch(self.pc_sel):
            with m.Case(PCSel.PC4):
                m.d.comb += next_pc.eq(pc_plus_4)
            with m.Case(PCSel.PC_IMM):
                m.d.comb += next_pc.eq(pc_plus_imm)
            with m.Case(PCSel.RS1_IMM):
                m.d.comb += next_pc.eq(alu.r)

        with m.If(self.pc_we):
            m.d.sync += self.pc.eq(next_pc)

        with m.Switch(self.alua_sel):
            with m.Case(AluASel.RS1):
                m.d.comb += alu.a.eq(regfile.rs1_data)
            with m.Case(AluASel.PC):
                m.d.comb += alu.a.eq(self.pc)

        with m.Switch(self.alub_sel):
            with m.Case(AluBSel.RS2):
                m.d.comb += alu.b.eq(regfile.rs2_data)
            with m.Case(AluBSel.IMM):
                m.d.comb += alu.b.eq(imm_gen.imm)

        with m.Switch(self.wb_sel):
            with m.Case(WbSel.ALU):
                m.d.comb += regfile.rd_data.eq(alu.r)
            with m.Case(WbSel.IMM):
                m.d.comb += regfile.rd_data.eq(imm_gen.imm)
            with m.Case(WbSel.PC4):
                m.d.comb += regfile.rd_data.eq(pc_plus_4)
            with m.Case(WbSel.DATA):
                m.d.comb += regfile.rd_data.eq(self.mem_rdata)

        return m
