from amaranth import *
from .. import isa
from ..constants import AluASel, AluBSel, AluOp, AluOpType, PCSel, WbSel
from ..branchctl import BranchControl
from ..aluctl import AluControl

class SingleCycleControlPath(Elaboratable):
    def __init__(self):
        self.opcode = Signal(isa.OPCODE_BITS)
        self.funct3 = Signal(3)
        self.funct7 = Signal(7)
        self.result_eqz = Signal()

        self.pc_we = Signal()
        self.reg_we = Signal()
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSel)
        self.mem_re = Signal()
        self.mem_we = Signal()
        self.wb_sel = Signal(WbSel)
        self.alu_op = Signal(AluOp)
        self.pc_sel = Signal(PCSel)

    def elaborate(self, platform):
        m = Module()

        take_branch = Signal()
        op_type = Signal(AluOpType)

        m.submodules.branch_control = branch_control = BranchControl()
        m.submodules.alu_control = alu_control = AluControl()

        m.d.comb += branch_control.funct3.eq(self.funct3)
        m.d.comb += branch_control.result_eqz.eq(self.result_eqz)
        m.d.comb += take_branch.eq(branch_control.take_branch)

        m.d.comb += alu_control.funct3.eq(self.funct3)
        m.d.comb += alu_control.funct7.eq(self.funct7)
        m.d.comb += alu_control.op_type.eq(op_type)
        m.d.comb += self.alu_op.eq(alu_control.alu_op)

        return m
