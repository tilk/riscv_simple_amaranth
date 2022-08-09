from amaranth import *
from .. import isa
from ..isa import Opcode
from ..constants import AluASel, AluBSelMC, AluOpType, WbSelMC, PCSelMC, InsnSel, AddrSel


class MultiCycleControl(Elaboratable):
    def __init__(self):
        self.opcode = Signal(isa.OPCODE_BITS)
        self.take_branch = Signal()
        self.mem_ack = Signal()

        self.pc_we = Signal()
        self.insn_we = Signal()
        self.data_we = Signal()
        self.reg_we = Signal()
        self.alu_we = Signal()
        self.alua_sel = Signal(AluASel)
        self.alub_sel = Signal(AluBSelMC)
        self.alu_op_type = Signal(AluOpType)
        self.mem_stb = Signal()
        self.mem_we = Signal()
        self.wb_sel = Signal(WbSelMC)
        self.pc_sel = Signal(PCSelMC)
        self.addr_sel = Signal(AddrSel)

    def elaborate(self, platform):
        m = Module()

        def use_alu(alua_sel: AluASel, alub_sel: AluBSelMC, alu_op_type: AluOpType):
            m.d.comb += self.alu_we.eq(1)
            m.d.comb += self.alua_sel.eq(alua_sel)
            m.d.comb += self.alub_sel.eq(alub_sel)
            m.d.comb += self.alu_op_type.eq(alu_op_type)
 
        def writeback(wb_sel: WbSelMC):
            m.d.comb += self.reg_we.eq(1)
            m.d.comb += self.wb_sel.eq(wb_sel)

        def update_pc(pc_sel: PCSelMC):
            m.d.comb += self.pc_we.eq(1)
            m.d.comb += self.pc_sel.eq(pc_sel)

        with m.FSM() as fsm:
            with m.State("FETCH"):
                with m.If(self.mem_ack):
                    use_alu(AluASel.PC, AluBSelMC.FOUR, AluOpType.ADD)
                    m.d.comb += self.insn_we.eq(1)
                    m.next = "DECODE"
            with m.State("DECODE"):
                use_alu(AluASel.PC, AluBSelMC.IMM, AluOpType.ADD)
                update_pc(PCSelMC.ALU_REG)
                with m.Switch(self.opcode):
                    with m.Case(Opcode.LOAD, Opcode.STORE):
                        m.next = "MEM_ADDR"
                    with m.Case(Opcode.BRANCH):
                        m.next = "BRANCH"
                    with m.Case(Opcode.JAL):
                        m.next = "JAL"
                    with m.Case(Opcode.JALR):
                        m.next = "JALR"
                    with m.Case(Opcode.LUI):
                        m.next = "LUI"
                    with m.Case(Opcode.OP):
                        m.next = "OP"
                    with m.Case(Opcode.OP_IMM):
                        m.next = "OP_IMM"
                    with m.Case(Opcode.AUIPC):
                        m.next = "ALU_WB"
            with m.State("OP"):
                use_alu(AluASel.RS1, AluBSelMC.RS2, AluOpType.OP)
                m.next = "ALU_WB"
            with m.State("OP_IMM"):
                use_alu(AluASel.RS1, AluBSelMC.IMM, AluOpType.OP_IMM)
                m.next = "ALU_WB"
            with m.State("LUI"):
                writeback(WbSelMC.IMM)
                m.next = "FETCH"
            with m.State("JAL"):
                update_pc(PCSelMC.ALU_REG)
                writeback(WbSelMC.PC)
                m.next = "FETCH"
            with m.State("JALR"):
                update_pc(PCSelMC.ALU)
                use_alu(AluASel.RS1, AluBSelMC.IMM, AluOpType.ADD)
                writeback(WbSelMC.PC)
                m.next = "FETCH"
            with m.State("ALU_WB"):
                writeback(WbSelMC.ALU_REG)
                m.next = "FETCH"
            with m.State("MEM_ADDR"):
                use_alu(AluASel.RS1, AluBSelMC.IMM, AluOpType.ADD)
                with m.Switch(self.opcode):
                    with m.Case(Opcode.LOAD):
                        m.next = "MEM_READ"
                    with m.Case(Opcode.STORE):
                        m.next = "MEM_WRITE"
            with m.State("MEM_READ"):
                with m.If(self.mem_ack):
                    m.d.comb += self.data_we.eq(1)
                    m.next = "MEM_WB"
            with m.State("MEM_WRITE"):
                m.d.comb += self.mem_stb.eq(1)
                m.d.comb += self.mem_we.eq(1)
                with m.If(self.mem_ack):
                    m.next = "FETCH"
            with m.State("MEM_WB"):
                writeback(WbSelMC.DATA)
                m.next = "FETCH"
            with m.State("BRANCH"):
                with m.If(self.take_branch):
                    update_pc(PCSelMC.ALU_REG)
                use_alu(AluASel.RS1, AluBSelMC.RS2, AluOpType.BRANCH)
                m.next = "FETCH"

        return m

