from amaranth import *
from .. import isa
from ..constants import AluASel, AluBSel, AluOp, InsnSel, PCSel, WbSel
from ..branchctl import BranchControl
from ..aluctl import AluControl
from .control import SingleCycleControl
from .busctl import SingleCycleBusControl

class SingleCycleControlPath(Elaboratable):
    def __init__(self):
        self.opcode = Signal(isa.OPCODE_BITS)
        self.funct3 = Signal(3)
        self.funct7 = Signal(7)
        self.result_eqz = Signal()
        self.insn_ack = Signal()
        self.mem_ack = Signal()

        self.insn_we = Signal()
        self.pc_we = Signal()
        self.reg_we = Signal()
        self.insn_sel = Signal(InsnSel)
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSel)
        self.mem_stb = Signal()
        self.mem_we = Signal()
        self.wb_sel = Signal(WbSel)
        self.alu_op = Signal(AluOp)
        self.pc_sel = Signal(PCSel)
        self.insn_stb = Signal()

    def elaborate(self, platform):
        m = Module()

        m.submodules.branch_control = branch_control = BranchControl()
        m.submodules.alu_control = alu_control = AluControl()
        m.submodules.control = control = SingleCycleControl()
        m.submodules.bus_control = bus_control = SingleCycleBusControl()

        m.d.comb += branch_control.funct3.eq(self.funct3)
        m.d.comb += branch_control.result_eqz.eq(self.result_eqz)

        m.d.comb += alu_control.funct3.eq(self.funct3)
        m.d.comb += alu_control.funct7.eq(self.funct7)
        m.d.comb += alu_control.op_type.eq(control.alu_op_type)
        m.d.comb += self.alu_op.eq(alu_control.alu_op)

        m.d.comb += control.opcode.eq(self.opcode)
        m.d.comb += control.take_branch.eq(branch_control.take_branch)
        m.d.comb += self.reg_we.eq(control.reg_we)
        m.d.comb += self.alua_sel.eq(control.alua_sel)
        m.d.comb += self.alub_sel.eq(control.alub_sel)
        m.d.comb += self.mem_stb.eq(control.mem_stb)
        m.d.comb += self.mem_we.eq(control.mem_we)
        m.d.comb += self.wb_sel.eq(control.wb_sel)
        m.d.comb += self.pc_sel.eq(control.pc_sel)

        m.d.comb += bus_control.insn_ack.eq(self.insn_ack)
        m.d.comb += bus_control.mem_ack.eq(self.mem_ack)
        m.d.comb += bus_control.mem_stb.eq(self.mem_stb)
        m.d.comb += self.insn_we.eq(bus_control.insn_we)
        m.d.comb += self.pc_we.eq(bus_control.pc_we)
        m.d.comb += self.insn_sel.eq(bus_control.insn_sel)
        m.d.comb += self.insn_stb.eq(bus_control.insn_stb)

        return m
