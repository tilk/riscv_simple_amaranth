from amaranth import *
from amaranth.sim import *
from .arch import RV32I
from .singlecycle.core import SingleCycleCore
from intelhex import IntelHex
import unittest


def hex_read(ih, addr):
    return ih[4*addr] | (ih[4*addr+1] << 8) | (ih[4*addr+2] << 16) | (ih[4*addr+3] << 24)


def text_memory(module, text):
    ih = IntelHex(text)
    def gen():
        yield Passive()
        while True:
            yield Settle()
            stb = yield module.insn_stb_o
            cyc = yield module.insn_cyc_o
            if stb and cyc:
                adr = yield module.insn_adr_o
                dat = hex_read(ih, adr)
                print("INSN: %.8x %.8x" % (adr, dat))
                yield module.insn_dat_i.eq(dat)
                yield module.insn_ack_i.eq(1)
            else:
                yield module.insn_ack_i.eq(0)
            yield
    return gen


def data_memory(module, data):
    ih = IntelHex(data)
    def gen():
        yield Active()
        while True:
            yield Settle()
            stb = yield module.mem_stb_o
            cyc = yield module.mem_cyc_o
            if stb and cyc:
                adr = yield module.mem_adr_o
                we = yield module.mem_we_o
                if we:
                    dat = yield module.mem_dat_o
                    print("DATA WRITE: %.8x %.8x" % (adr, dat))
                else:
                    dat = hex_read(ih, adr)
                    print("DATA READ: %.8x %.8x" % (adr, dat))
                    yield module.mem_dat_i.eq(dat)
                yield module.mem_ack_i.eq(1)
            else:
                yield module.mem_ack_i.eq(0)
            yield
    return gen


def test_runner(module, text, data):
    class TestRunner(unittest.TestCase):
        def runTest(self):
            sim = Simulator(module)
            sim.add_clock(1e-6)
            sim.add_sync_process(text_memory(module, text))
            sim.add_sync_process(data_memory(module, data))
            with sim.write_vcd("test.vcd"):
                sim.run()

    return TestRunner


core = SingleCycleCore(RV32I())

add = test_runner(core, "tests/add.text.hex", "tests/add.data.hex")
addi = test_runner(core, "tests/addi.text.hex", "tests/addi.data.hex")
