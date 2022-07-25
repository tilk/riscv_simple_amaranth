class ArchVariant:
    BIT_WIDTH: int
    REGS_BITS: int
    REGS: int


class RV32I(ArchVariant):
    BIT_WIDTH = 32
    REGS_BITS = 5
    REGS = 2**REGS_BITS

