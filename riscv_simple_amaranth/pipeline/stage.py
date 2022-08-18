from amaranth import *
from enum import IntEnum
  
  
class Stage(IntEnum):
    IF = 0
    ID = 1
    EX = 2
    MEM = 3
    WB = 4
