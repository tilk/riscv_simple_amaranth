from amaranth import *
from .. import isa
from ..isa import Opcode
from ..constants import AluASel, AluBSel, AluOpType, PCSel, WbSel, JumpType


class PipelineControl(Elaboratable):
    def __init__(self):
        self.opcode = Signal(Opcode)
        self.take_branch = Signal()
        self.jump_type = Signal(JumpType)

        self.reg_we = Signal()
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSel)
        self.alu_op_type = Signal(AluOpType)
        self.mem_stb = Signal()
        self.mem_we = Signal()
        self.wb_sel = Signal(WbSel)
        self.pc_sel = Signal(PCSel)
        self.do_jump = Signal()
        self.jump_type_ex = Signal(JumpType)

    def elaborate(self, platform):
        m = Module()

        def use_alu(alua_sel: AluASel, alub_sel: AluBSel, alu_op_type: AluOpType):
            m.d.comb += self.alua_sel.eq(alua_sel)
            m.d.comb += self.alub_sel.eq(alub_sel)
            m.d.comb += self.alu_op_type.eq(alu_op_type)

        def writeback(wb_sel: WbSel):
            m.d.comb += self.reg_we.eq(1)
            m.d.comb += self.wb_sel.eq(wb_sel)

        def jump(pc_sel: PCSel):
            m.d.comb += self.do_jump.eq(1)
            m.d.comb += self.pc_sel.eq(pc_sel)

        with m.Switch(self.opcode):
            with m.Case(Opcode.OP):
                use_alu(AluASel.RS1, AluBSel.RS2, AluOpType.OP)
                writeback(WbSel.ALU)
            with m.Case(Opcode.OP_IMM):
                use_alu(AluASel.RS1, AluBSel.IMM, AluOpType.OP_IMM)
                writeback(WbSel.ALU)
            with m.Case(Opcode.BRANCH):
                use_alu(AluASel.RS1, AluBSel.RS2, AluOpType.BRANCH)
                m.d.comb += self.jump_type.eq(JumpType.BRANCH)
            with m.Case(Opcode.JAL):
                use_alu(AluASel.PC, AluBSel.IMM, AluOpType.ADD)
                writeback(WbSel.PC4)
                m.d.comb += self.jump_type.eq(JumpType.JAL)
            with m.Case(Opcode.JALR):
                use_alu(AluASel.RS1, AluBSel.IMM, AluOpType.ADD)
                writeback(WbSel.PC4)
                m.d.comb += self.jump_type.eq(JumpType.JALR)
            with m.Case(Opcode.LOAD):
                use_alu(AluASel.RS1, AluBSel.IMM, AluOpType.ADD)
                writeback(WbSel.DATA)
                m.d.comb += self.mem_stb.eq(1)
            with m.Case(Opcode.STORE):
                use_alu(AluASel.RS1, AluBSel.IMM, AluOpType.ADD)
                m.d.comb += self.mem_stb.eq(1)
                m.d.comb += self.mem_we.eq(1)
            with m.Case(Opcode.LUI):
                writeback(WbSel.IMM)
            with m.Case(Opcode.AUIPC):
                use_alu(AluASel.PC, AluBSel.IMM, AluOpType.ADD)
                writeback(WbSel.ALU)

        with m.Switch(self.jump_type_ex):
            with m.Case(JumpType.BRANCH):
                with m.If(self.take_branch):
                    jump(PCSel.PC_IMM)
            with m.Case(JumpType.JAL):
                jump(PCSel.PC_IMM)
            with m.Case(JumpType.JALR):
                jump(PCSel.RS1_IMM)

        return m
