from amaranth import *
from amaranth.sim import *
from .arch import RV32I
from .singlecycle.core import SingleCycleCore
import unittest


def text_memory(module, text):
    pass


def data_memory(module, data):
    pass


def test_runner(module, text, data):
    class TestRunner(unittest.TestCase):
        def runTest(self):
            sim = Simulator(module)
            sim.add_clock(1e-6)
            sim.add_sync_process(text_memory(module, text))
            sim.add_sync_process(data_memory(module, data))
            sim.run()

    return TestRunner


core = SingleCycleCore(RV32I())
x = test_runner(core, "a", "b")
y = test_runner(core, "c", "d")
