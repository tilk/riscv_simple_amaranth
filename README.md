# riscv_simple_amaranth

This is a collection of simple RISC-V (RV32I) cores for teaching purposes.
They are written in [Amaranth](https://amaranth-lang.org/), a HDL implemented as a Python DSL (Domain-Specific Language).
The implementation is very simple and mostly in line with how RISC cores are usually presented in introductory textbooks.
The cores use Wishbone as their memory bus, so that they can be synthesized to hardware for presentation purposes.

Three cores are implemented:
- A single-cycle core (one instruction per cycle, Harvard architecture),
- A multi-cycle core (variable number of cycles for different instructions, von Neumann architecture),
- A pipelined core (five-stage pipeline, Harvard architecture).

The cores are verified using [riscv-tests](https://github.com/riscv/riscv-tests).
