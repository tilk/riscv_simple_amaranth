
CC=riscv64-unknown-elf-gcc
LD=riscv64-unknown-elf-ld
SREC_CAT=srec_cat
OBJCOPY=riscv64-unknown-elf-objcopy
CFLAGS=-mabi=ilp32 -march=rv32i
LDFLAGS=-Tlink.ld -melf32lriscv
SRCS=$(wildcard *.S)
OBJS=$(SRCS:.S=.o)
ELFS=$(SRCS:.S=.elf)
HEXS=$(SRCS:.S=.text.hex) $(SRCS:.S=.data.hex)

all: ${HEXS}

%.o: %.S test_macros.h riscv_test.h
	${CC} -c ${CFLAGS} -o $@ $<

%.elf: %.o 
	${LD} ${LDFLAGS} $< -o $@

%.text.hex: %.elf
	${OBJCOPY} -O ihex $< $@ -j .init -j .text --change-addresses -0x400000

%.data.hex: %.elf
	${OBJCOPY} -O ihex $< $@ -j .data -j .eh_frame -j .fini_array -j .init_array --change-addresses -0x80000000

clean:
	rm -f ${OBJS} ${ELFS} ${HEXS}

