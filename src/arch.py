class ArchVariant:
    BYTE_WIDTH_BITS: int
    REGS_BITS: int
    
    @property
    def BYTE_WIDTH(self) -> int:
        return 2 ** self.BYTE_WIDTH_BITS

    @property
    def BIT_WIDTH(self) -> int:
        return 8 * self.BYTE_WIDTH
    
    @property
    def REGS(self) -> int:
        return 2 ** self.REGS_BITS


class RV32I(ArchVariant):
    BYTE_WIDTH_BITS = 2
    REGS_BITS = 5

