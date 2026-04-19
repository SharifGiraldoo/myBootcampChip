# Makefile - Test para tt_um_alu7b
# Bootcamp Diseño y Fabricación de Chips - UTP 2026
# Ver https://docs.cocotb.org/en/stable/quickstart.html

# Defaults
SIM ?= icarus
FST ?= -fst
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src

# IMPORTANTE: listar los archivos fuente individualmente (sin project.v)
# para evitar redefinición de módulos cuando iverilog compila con `include.
# El orden importa: alu_7b.v debe ir antes que tt_um_alu7b.v porque
# tt_um_alu7b instancia alu_7b.
PROJECT_SOURCES = alu_7b.v tt_um_alu7b.v

ifneq ($(GATES),yes)

# Simulación RTL
SIM_BUILD        = sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

else

# Simulación Gate Level
SIM_BUILD        = sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DUSE_POWER_PINS
COMPILE_ARGS    += -DSIM
COMPILE_ARGS    += -DUNIT_DELAY=\#1
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Directorio de includes
COMPILE_ARGS += -I$(SRC_DIR)

# Testbench
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# Módulo de prueba cocotb
COCOTB_TEST_MODULES = test

# Reglas de cocotb
include $(shell cocotb-config --makefiles)/Makefile.sim