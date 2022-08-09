from amaranth import *
from .. import isa
from ..constants import AluASel, AluBSelMC, AluOp, InsnSel, PCSelMC, WbSelMC, AddrSel
from ..branchctl import BranchControl
from ..aluctl import AluControl
from .control import MultiCycleControl

class MultiCycleControlPath(Elaboratable):
    def __init__(self):
        self.opcode = Signal(isa.OPCODE_BITS)
        self.funct3 = Signal(3)
        self.funct7 = Signal(7)
        self.result_eqz = Signal()
        self.mem_ack = Signal()

        self.pc_we = Signal()
        self.insn_we = Signal()
        self.data_we = Signal()
        self.reg_we = Signal()
        self.alu_we = Signal()
        self.addr_sel = Signal(AddrSel)
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSelMC)
        self.mem_stb = Signal()
        self.mem_we = Signal()
        self.wb_sel = Signal(WbSelMC)
        self.alu_op = Signal(AluOp)
        self.pc_sel = Signal(PCSelMC)

    def elaborate(self, platform):
        m = Module()

        m.submodules.branch_control = branch_control = BranchControl()
        m.submodules.alu_control = alu_control = AluControl()
        m.submodules.control = control = MultiCycleControl()

        m.d.comb += branch_control.funct3.eq(self.funct3)
        m.d.comb += branch_control.result_eqz.eq(self.result_eqz)

        m.d.comb += alu_control.funct3.eq(self.funct3)
        m.d.comb += alu_control.funct7.eq(self.funct7)
        m.d.comb += alu_control.op_type.eq(control.alu_op_type)
        m.d.comb += self.alu_op.eq(alu_control.alu_op)

        m.d.comb += control.opcode.eq(self.opcode)
        m.d.comb += control.take_branch.eq(branch_control.take_branch)
        m.d.comb += control.mem_ack.eq(self.mem_ack)
        m.d.comb += self.pc_we.eq(control.pc_we)
        m.d.comb += self.insn_we.eq(control.insn_we)
        m.d.comb += self.data_we.eq(control.data_we)
        m.d.comb += self.reg_we.eq(control.reg_we)
        m.d.comb += self.alu_we.eq(control.alu_we)
        m.d.comb += self.addr_sel.eq(control.addr_sel)
        m.d.comb += self.alua_sel.eq(control.alua_sel)
        m.d.comb += self.alub_sel.eq(control.alub_sel)
        m.d.comb += self.mem_stb.eq(control.mem_stb)
        m.d.comb += self.mem_we.eq(control.mem_we)
        m.d.comb += self.wb_sel.eq(control.wb_sel)
        m.d.comb += self.pc_sel.eq(control.pc_sel)


        return m
