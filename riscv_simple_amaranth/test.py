from amaranth import *
from amaranth.sim import *
from .arch import RV32I
from .singlecycle.core import SingleCycleCore
from .multicycle.core import MultiCycleCore
from .pipeline.core import PipelineCore
from intelhex import IntelHex
import unittest
import glob
import random
import os


MAX_WAIT_CYCLES = 2


def hex_read(ih, addr):
    return ih[addr] | (ih[addr + 1] << 8) | (ih[addr + 2] << 16) | (ih[addr + 3] << 24)


def hex_write(ih, addr, value):
    ih[addr] = value & 0xFF
    ih[addr + 1] = (value >> 8) & 0xFF
    ih[addr + 2] = (value >> 16) & 0xFF
    ih[addr + 3] = (value >> 24) & 0xFF


def debugprint(s):
    if "MEM_DEBUG" in os.environ:
        print(s)


def load_tests(loader, tests, pattern):
    class TestRunner(unittest.TestCase):
        def __init__(self, module, testid, text, data):
            super().__init__()
            self.module = module
            self.testid = testid
            self.text = text
            self.data = data

        def text_memory(self, module, text):
            ih = IntelHex(text)

            def gen():
                yield Passive()
                while True:
                    yield Settle()
                    stb = yield module.insn_stb_o
                    cyc = yield module.insn_cyc_o
                    if stb and cyc:
                        adr = yield module.insn_adr_o
                        addr = adr << 2
                        addr_off = addr - 0x400000
                        self.assertGreaterEqual(addr, 0x400000)
                        self.assertLess(addr, 0x80000000)
                        dat = hex_read(ih, addr_off)
                        debugprint("INSN: %.8x %.8x" % (addr, dat))
                        for _ in range(random.randint(0, MAX_WAIT_CYCLES)):
                            yield module.insn_ack_i.eq(0)
                            yield
                        yield module.insn_dat_i.eq(dat)
                        yield module.insn_ack_i.eq(1)
                    else:
                        yield module.insn_ack_i.eq(0)
                    yield

            return gen

        def data_memory(self, module, data):
            ih = IntelHex(data)

            def gen():
                yield Active()
                while True:
                    yield Settle()
                    yield Settle()
                    stb = yield module.mem_stb_o
                    cyc = yield module.mem_cyc_o
                    if stb and cyc:
                        adr = yield module.mem_adr_o
                        we = yield module.mem_we_o
                        addr = adr << 2
                        addr_off = addr - 0x80000000
                        self.assertGreaterEqual(addr, 0x80000000)
                        if we:
                            dat = yield module.mem_dat_o
                            hex_write(ih, addr_off, dat)
                            debugprint("DATA WRITE: %.8x %.8x" % (addr, dat))
                            if adr << 2 == 0xFFFFFFF0:
                                self.assertEqual(dat, 1)
                                yield Passive()
                        else:
                            dat = hex_read(ih, addr_off)
                            debugprint("DATA READ: %.8x %.8x" % (addr, dat))
                            yield module.mem_dat_i.eq(dat)
                        for _ in range(random.randint(0, MAX_WAIT_CYCLES)):
                            yield module.mem_ack_i.eq(0)
                            yield
                        yield module.mem_ack_i.eq(1)
                    else:
                        yield module.mem_ack_i.eq(0)
                    yield

            return gen

        def runTest(self):
            debugprint(self.testid)
            sim = Simulator(self.module)
            sim.add_clock(1e-9)
            sim.add_sync_process(self.text_memory(self.module, self.text))
            sim.add_sync_process(self.data_memory(self.module, self.data))
            with sim.write_vcd("tests/%s.vcd" % self.testid):
                sim.run()

        def id(self):
            return self.testid

    class TestRunnerVN(unittest.TestCase):
        def __init__(self, module, testid, text, data):
            super().__init__()
            self.module = module
            self.testid = testid
            self.text = text
            self.data = data

        def memory(self, module, text, data):
            ih_text = IntelHex(text)
            ih_data = IntelHex(data)

            def gen():
                yield Active()
                while True:
                    yield Settle()
                    yield Settle()
                    stb = yield module.mem_stb_o
                    cyc = yield module.mem_cyc_o
                    if stb and cyc:
                        adr = yield module.mem_adr_o
                        we = yield module.mem_we_o
                        addr = adr << 2
                        if addr >= 0x80000000:
                            ih = ih_data
                            addr_off = addr - 0x80000000
                        else:
                            ih = ih_text
                            addr_off = addr - 0x400000
                            self.assertGreaterEqual(addr, 0x400000)
                        if we:
                            dat = yield module.mem_dat_o
                            hex_write(ih, addr_off, dat)
                            debugprint("DATA WRITE: %.8x %.8x" % (addr, dat))
                            self.assertIs(ih, ih_data)
                            if adr << 2 == 0xFFFFFFF0:
                                self.assertEqual(dat, 1)
                                yield Passive()
                        else:
                            dat = hex_read(ih, addr_off)
                            debugprint("DATA READ: %.8x %.8x" % (addr, dat))
                            yield module.mem_dat_i.eq(dat)
                        for _ in range(random.randint(0, MAX_WAIT_CYCLES)):
                            yield module.mem_ack_i.eq(0)
                            yield
                        yield module.mem_ack_i.eq(1)
                    else:
                        yield module.mem_ack_i.eq(0)
                    yield

            return gen

        def runTest(self):
            debugprint(self.testid)
            sim = Simulator(self.module)
            sim.add_clock(1e-9)
            sim.add_sync_process(self.memory(self.module, self.text, self.data))
            with sim.write_vcd("tests/%s.vcd" % self.testid):
                sim.run()

        def id(self):
            return self.testid

    suite = unittest.TestSuite()
    for (corename, core, runner) in [
        ("singlecycle", SingleCycleCore(RV32I()), TestRunner),
        ("multicycle", MultiCycleCore(RV32I()), TestRunnerVN),
        ("pipeline", PipelineCore(RV32I()), TestRunner),
    ]:
        for name in glob.glob("tests/*.text.hex"):
            dname = name.replace("text", "data")
            testid = name[6:-9]
            suite.addTest(runner(core, "%s_%s" % (testid, corename), name, dname))
    return suite
