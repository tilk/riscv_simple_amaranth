from amaranth import *
from .. import isa
from ..constants import AluASel, AluBSel, AluOp, InsnSel, PCSel, WbSel, JumpType
from ..branchctl import BranchControl
from ..aluctl import AluControl
from .stage import Stage, WithPipeline
from .control import PipelineControl
#from .busctl import PipelineBusControl


class PipelineControlPath(Elaboratable, WithPipeline):
    def __init__(self):
        self.opcode = Signal(isa.OPCODE_BITS)
        self.funct3 = Signal(3)
        self.funct7 = Signal(7)
        self.result_eqz = Signal()
        self.ex_funct3 = Signal(3)
        self.want_stall = Signal()
        self.insn_valid = Signal()
        self.mem_valid = Signal()

        self.insn_we = Signal()
        self.pc_we = Signal()
        self.reg_we = Signal()
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSel)
        self.mem_request = Signal()
        self.mem_stb = Signal()
        self.mem_we = Signal()
        self.wb_sel = Signal(WbSel)
        self.alu_op = Signal(AluOp)
        self.pc_sel = Signal(PCSel)
        self.insn_request = Signal()
        self.step = Signal()
        self.stall = Signal()
        self.insn_kill = Signal()

    def elaborate(self, platform):
        m = Module()

        m.submodules.branch_control = branch_control = BranchControl()
        m.submodules.alu_control = alu_control = AluControl()
        m.submodules.control = control = PipelineControl()
#        m.submodules.bus_control = bus_control = PipelineBusControl()

        jump_type = self.pipeline_signal(m, Stage.ID, Stage.EX, control.jump_type, bubble_value = JumpType.NONE)

        m.d.comb += branch_control.funct3.eq(self.ex_funct3)
        m.d.comb += branch_control.result_eqz.eq(self.result_eqz)

        m.d.comb += alu_control.funct3.eq(self.funct3)
        m.d.comb += alu_control.funct7.eq(self.funct7)
        m.d.comb += alu_control.op_type.eq(control.alu_op_type)
        m.d.comb += self.alu_op.eq(alu_control.alu_op)

        m.d.comb += control.opcode.eq(self.opcode)
        m.d.comb += control.take_branch.eq(branch_control.take_branch)
        m.d.comb += control.jump_type_ex.eq(jump_type[Stage.EX])
        m.d.comb += self.reg_we.eq(control.reg_we)
        m.d.comb += self.alua_sel.eq(control.alua_sel)
        m.d.comb += self.alub_sel.eq(control.alub_sel)
        m.d.comb += self.mem_we.eq(control.mem_we)
        m.d.comb += self.mem_stb.eq(control.mem_stb)
        m.d.comb += self.wb_sel.eq(control.wb_sel)
        m.d.comb += self.pc_sel.eq(control.pc_sel)
        m.d.comb += self.stall.eq(control.do_jump | self.want_stall)

        m.d.comb += self.insn_request.eq(~self.want_stall)
        m.d.comb += self.step.eq((~self.insn_request | self.insn_valid) & (~self.mem_request | self.mem_valid))
        m.d.comb += self.pc_we.eq(self.step & (self.insn_request | control.do_jump))
        m.d.comb += self.insn_kill.eq(control.do_jump)

#        m.d.comb += bus_control.insn_ack.eq(self.insn_ack)
#        m.d.comb += bus_control.mem_ack.eq(self.mem_ack)
#        m.d.comb += bus_control.mem_stb.eq(self.mem_stb)
#        m.d.comb += self.insn_we.eq(bus_control.insn_we)
#        m.d.comb += self.pc_we.eq(bus_control.pc_we)
#        m.d.comb += self.insn_sel.eq(bus_control.insn_sel)
#        m.d.comb += self.insn_stb.eq(bus_control.insn_stb)

        return m
