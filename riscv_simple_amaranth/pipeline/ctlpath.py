from amaranth import *
from .. import isa
from ..constants import AluASel, AluBSel, AluOp, PCSel, WbSel, JumpType
from ..branchctl import BranchControl
from ..aluctl import AluControl
from .stage import Stage, WithPipeline
from .control import PipelineControl
from .execctl import PipelineExecControl


class PipelineControlPath(Elaboratable, WithPipeline):
    def __init__(self):
        self.opcode = Signal(isa.OPCODE_BITS)
        self.funct3 = Signal(3)
        self.funct7 = Signal(7)
        self.result_eqz = Signal()
        self.ex_funct3 = Signal(3)
        self.want_stall = Signal()
        self.insn_valid = Signal()
        self.mem_request = Signal()
        self.mem_valid = Signal()

        self.insn_we = Signal()
        self.pc_we = Signal()
        self.reg_we = Signal()
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSel)
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
        m.submodules.exec_control = exec_control = PipelineExecControl()

        jump_type = self.pipeline_signal(m, Stage.ID, Stage.EX, control.jump_type, bubble_value=JumpType.NONE)

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

        m.d.comb += exec_control.insn_valid.eq(self.insn_valid)
        m.d.comb += exec_control.mem_request.eq(self.mem_request)
        m.d.comb += exec_control.mem_valid.eq(self.mem_valid)
        m.d.comb += exec_control.do_jump.eq(control.do_jump)
        m.d.comb += exec_control.want_stall.eq(self.want_stall)
        m.d.comb += self.stall.eq(exec_control.stall)
        m.d.comb += self.insn_request.eq(exec_control.insn_request)
        m.d.comb += self.step.eq(exec_control.step)
        m.d.comb += self.pc_we.eq(exec_control.pc_we)
        m.d.comb += self.insn_kill.eq(exec_control.insn_kill)

        return m
