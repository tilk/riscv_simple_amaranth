from amaranth import *
from constants import AluOpType, AluOp
from isa import Funct3Alu, Funct3Branch


class AluControl(Elaboratable):
    def __init__(self):
        self.op_type = Signal(AluOpType)
        self.funct3 = Signal(3)
        self.funct7 = Signal(7)
        self.alu_op = Signal(AluOp)

    def elaborate(self, platform):
        m = Module()

        alu_op_default = Signal(AluOp)
        alu_op_secondary = Signal(AluOp)
        alu_op_op = Signal(AluOp)
        alu_op_op_imm = Signal(AluOp)
        alu_op_branch = Signal(AluOp)

        with m.Switch(self.funct3):
            with m.Case(Funct3Alu.ADD):
                m.d.comb += alu_op_default.eq(AluOp.ADD)
            with m.Case(Funct3Alu.SLL):
                m.d.comb += alu_op_default.eq(AluOp.SLL)
            with m.Case(Funct3Alu.SLT):
                m.d.comb += alu_op_default.eq(AluOp.SLT)
            with m.Case(Funct3Alu.SLTU):
                m.d.comb += alu_op_default.eq(AluOp.SLTU)
            with m.Case(Funct3Alu.XOR):
                m.d.comb += alu_op_default.eq(AluOp.XOR)
            with m.Case(Funct3Alu.SRL):
                m.d.comb += alu_op_default.eq(AluOp.SRL)
            with m.Case(Funct3Alu.OR):
                m.d.comb += alu_op_default.eq(AluOp.OR)
            with m.Case(Funct3Alu.AND):
                m.d.comb += alu_op_default.eq(AluOp.AND)

        with m.Switch(self.funct3):
            with m.Case(Funct3Alu.ADD):
                m.d.comb += alu_op_secondary.eq(AluOp.ADD)
            with m.Case(Funct3Alu.SRL):
                m.d.comb += alu_op_secondary.eq(AluOp.SRL)

        with m.Switch(self.funct3):
            with m.Case(Funct3Branch.EQ):
                m.d.comb += alu_op_branch.eq(AluOp.SEQ)
            with m.Case(Funct3Branch.NE):
                m.d.comb += alu_op_branch.eq(AluOp.SEQ)
            with m.Case(Funct3Branch.LT):
                m.d.comb += alu_op_branch.eq(AluOp.SLT)
            with m.Case(Funct3Branch.GE):
                m.d.comb += alu_op_branch.eq(AluOp.SLT)
            with m.Case(Funct3Branch.LTU):
                m.d.comb += alu_op_branch.eq(AluOp.SLTU)
            with m.Case(Funct3Branch.GEU):
                m.d.comb += alu_op_branch.eq(AluOp.SLTU)

        with m.If(self.funct7[5]):
            m.d.comb += alu_op_op.eq(alu_op_secondary)
        with m.Else():
            m.d.comb += alu_op_op.eq(alu_op_default)

        with m.If(self.funct7[5] & self.funct3[0:2] == 1):
            m.d.comb += alu_op_op_imm.eq(alu_op_secondary)
        with m.Else():
            m.d.comb += alu_op_op_imm.eq(alu_op_default)

        with m.Switch(self.op_type):
            with m.Case(AluOpType.ADD):
                m.d.comb += self.alu_op.eq(AluOp.ADD)
            with m.Case(AluOpType.OP):
                m.d.comb += self.alu_op.eq(alu_op_op)
            with m.Case(AluOpType.OP_IMM):
                m.d.comb += self.alu_op.eq(alu_op_op_imm)
            with m.Case(AluOpType.BRANCH):
                m.d.comb += self.alu_op.eq(alu_op_branch)

        return m
