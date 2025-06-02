from amaranth import *
from amaranth.sim import *
from amaranth.sim._async import TestbenchContext
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

            async def gen(sim: TestbenchContext):
                while True:
                    stb = sim.get(module.insn_stb_o)
                    cyc = sim.get(module.insn_cyc_o)
                    if stb and cyc:
                        adr = sim.get(module.insn_adr_o)
                        addr = adr << 2
                        addr_off = addr - 0x400000
                        self.assertGreaterEqual(addr, 0x400000)
                        self.assertLess(addr, 0x80000000)
                        dat = hex_read(ih, addr_off)
                        debugprint("INSN: %.8x %.8x" % (addr, dat))
                        for _ in range(random.randint(0, MAX_WAIT_CYCLES)):
                            sim.set(module.insn_ack_i, 0)
                            await sim.tick()
                        sim.set(module.insn_dat_i, dat)
                        sim.set(module.insn_ack_i, 1)
                    else:
                        sim.set(module.insn_ack_i, 0)
                    await sim.tick()

            return gen

        def data_memory(self, module, data):
            ih = IntelHex(data)

            async def gen(sim: TestbenchContext):
                while True:
                    stb = sim.get(module.mem_stb_o)
                    cyc = sim.get(module.mem_cyc_o)
                    if stb and cyc:
                        adr = sim.get(module.mem_adr_o)
                        we = sim.get(module.mem_we_o)
                        addr = adr << 2
                        addr_off = addr - 0x80000000
                        self.assertGreaterEqual(addr, 0x80000000)
                        if we:
                            dat = sim.get(module.mem_dat_o)
                            hex_write(ih, addr_off, dat)
                            debugprint("DATA WRITE: %.8x %.8x" % (addr, dat))
                            if adr << 2 == 0xFFFFFFF0:
                                self.assertEqual(dat, 1)
                                return
                        else:
                            dat = hex_read(ih, addr_off)
                            debugprint("DATA READ: %.8x %.8x" % (addr, dat))
                            sim.set(module.mem_dat_i, dat)
                        for _ in range(random.randint(0, MAX_WAIT_CYCLES)):
                            sim.set(module.mem_ack_i, 0)
                            await sim.tick()
                        sim.set(module.mem_ack_i, 1)
                    else:
                        sim.set(module.mem_ack_i, 0)
                    await sim.tick()

            return gen

        def runTest(self):
            debugprint(self.testid)
            sim = Simulator(self.module)
            sim.add_clock(1e-9)
            sim.add_testbench(self.text_memory(self.module, self.text), background=True)
            sim.add_testbench(self.data_memory(self.module, self.data))
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

            async def gen(sim: TestbenchContext):
                while True:
                    stb = sim.get(module.mem_stb_o)
                    cyc = sim.get(module.mem_cyc_o)
                    if stb and cyc:
                        adr = sim.get(module.mem_adr_o)
                        we = sim.get(module.mem_we_o)
                        addr = adr << 2
                        if addr >= 0x80000000:
                            ih = ih_data
                            addr_off = addr - 0x80000000
                        else:
                            ih = ih_text
                            addr_off = addr - 0x400000
                            self.assertGreaterEqual(addr, 0x400000)
                        if we:
                            dat = sim.get(module.mem_dat_o)
                            hex_write(ih, addr_off, dat)
                            debugprint("DATA WRITE: %.8x %.8x" % (addr, dat))
                            self.assertIs(ih, ih_data)
                            if adr << 2 == 0xFFFFFFF0:
                                self.assertEqual(dat, 1)
                                return
                        else:
                            dat = hex_read(ih, addr_off)
                            debugprint("DATA READ: %.8x %.8x" % (addr, dat))
                            sim.set(module.mem_dat_i, dat)
                        for _ in range(random.randint(0, MAX_WAIT_CYCLES)):
                            sim.set(module.mem_ack_i, 0)
                            await sim.tick()
                        sim.set(module.mem_ack_i, 1)
                    else:
                        sim.set(module.mem_ack_i, 0)
                    await sim.tick()

            return gen

        def runTest(self):
            debugprint(self.testid)
            sim = Simulator(self.module)
            sim.add_clock(1e-9)
            sim.add_testbench(self.memory(self.module, self.text, self.data))
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
