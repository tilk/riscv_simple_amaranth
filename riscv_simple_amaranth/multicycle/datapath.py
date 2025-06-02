from amaranth import *
from .. import isa
from ..constants import AluASel, AluBSelMC, WbSelMC, AluOp, PCSelMC, InsnSel, AddrSel
from ..arch import ArchVariant
from ..alu import Alu
from ..regfile import RegFile
from ..imm_gen import ImmGen
from ..insn_decoder import InsnDecoder


class MultiCycleDataPath(Elaboratable):
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
        self.alu_we = Signal()
        self.data_we = Signal()
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSelMC)
        self.alu_op = Signal(AluOp)
        self.wb_sel = Signal(WbSelMC)
        self.pc_sel = Signal(PCSelMC)
        self.addr_sel = Signal(AddrSel)

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

        insn = Signal(isa.INSN_BITS)
        alu_reg = Signal.like(alu.r)
        data_reg = Signal.like(self.mem_rdata)
        rs1_reg = Signal.like(regfile.rs1_data)
        rs2_reg = Signal.like(regfile.rs2_data)
        pc = Signal(self.variant.BIT_WIDTH, init=0x400000)
        next_pc = Signal.like(pc)

        with m.If(self.insn_we):
            m.d.sync += insn.eq(self.mem_rdata)

        with m.If(self.pc_we):
            m.d.sync += pc.eq(next_pc)

        with m.If(self.alu_we):
            m.d.sync += alu_reg.eq(alu.r)

        with m.If(self.data_we):
            m.d.sync += data_reg.eq(self.mem_rdata)

        m.d.sync += rs1_reg.eq(regfile.rs1_data)
        m.d.sync += rs2_reg.eq(regfile.rs2_data)

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

        with m.Switch(self.addr_sel):
            with m.Case(AddrSel.PC):
                m.d.comb += self.mem_addr.eq(pc)
            with m.Case(AddrSel.ALU_REG):
                m.d.comb += self.mem_addr.eq(alu_reg)

        with m.Switch(self.alua_sel):
            with m.Case(AluASel.RS1):
                m.d.comb += alu.a.eq(rs1_reg)
            with m.Case(AluASel.PC):
                m.d.comb += alu.a.eq(pc)

        with m.Switch(self.alub_sel):
            with m.Case(AluBSelMC.RS2):
                m.d.comb += alu.b.eq(rs2_reg)
            with m.Case(AluBSelMC.IMM):
                m.d.comb += alu.b.eq(imm_gen.imm)
            with m.Case(AluBSelMC.FOUR):
                m.d.comb += alu.b.eq(4)

        with m.Switch(self.wb_sel):
            with m.Case(WbSelMC.ALU_REG):
                m.d.comb += regfile.rd_data.eq(alu_reg)
            with m.Case(WbSelMC.IMM):
                m.d.comb += regfile.rd_data.eq(imm_gen.imm)
            with m.Case(WbSelMC.PC):
                m.d.comb += regfile.rd_data.eq(pc)
            with m.Case(WbSelMC.DATA):
                m.d.comb += regfile.rd_data.eq(data_reg)

        with m.Switch(self.pc_sel):
            with m.Case(PCSelMC.ALU_REG):
                m.d.comb += next_pc.eq(alu_reg)
            with m.Case(PCSelMC.ALU):
                m.d.comb += next_pc.eq(alu.r)

        return m
