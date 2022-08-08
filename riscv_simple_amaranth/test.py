from amaranth import *
from amaranth.sim import *
from .arch import RV32I
from .singlecycle.core import SingleCycleCore
from intelhex import IntelHex
import unittest
import glob


def hex_read(ih, addr):
    return ih[addr] | (ih[addr+1] << 8) | (ih[addr+2] << 16) | (ih[addr+3] << 24)


def hex_write(ih, addr, value):
    ih[addr] = value & 0xff
    ih[addr+1] = (value >> 8) & 0xff
    ih[addr+2] = (value >> 16) & 0xff
    ih[addr+3] = (value >> 24) & 0xff


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
                        print("INSN: %.8x %.8x" % (addr, dat))
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
                            print("DATA WRITE: %.8x %.8x" % (addr, dat))
                            if adr << 2 == 0xfffffff0:
                                self.assertEqual(dat, 1)
                                yield Passive()
                        else:
                            dat = hex_read(ih, addr_off)
                            print("DATA READ: %.8x %.8x" % (addr, dat))
                            yield module.mem_dat_i.eq(dat)
                        yield module.mem_ack_i.eq(1)
                    else:
                        yield module.mem_ack_i.eq(0)
                    yield
            return gen
    
        def runTest(self):
            print(self.testid)
            sim = Simulator(self.module)
            sim.add_clock(1e-9)
            sim.add_sync_process(self.text_memory(self.module, self.text))
            sim.add_sync_process(self.data_memory(self.module, self.data))
            with sim.write_vcd("tests/%s.vcd" % self.testid):
                sim.run()

        def id(self):
            return self.testid


    core = SingleCycleCore(RV32I())
    suite = unittest.TestSuite()
    for name in glob.glob("tests/*.text.hex"):
        dname = name.replace("text", "data")
        testid = name[6:-9]
        suite.addTest(TestRunner(core, testid, name, dname))
    return suite
