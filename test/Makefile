# Makefile - Test para tt_um_alu7b
# Bootcamp Diseño y Fabricación de Chips - UTP 2026
# Ver https://docs.cocotb.org/en/stable/quickstart.html

# Defaults
SIM ?= icarus
FST ?= -fst
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src

# IMPORTANTE: project.v incluye alu_7b.v y tt_um_alu7b.v via `include
# Por eso solo se lista project.v aquí.
PROJECT_SOURCES = project.v

ifneq ($(GATES),yes)

# Simulación RTL
SIM_BUILD        = sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

else

# Simulación a nivel de compuertas (Gate Level)
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

# Permitir includes entre src/ y test/
COMPILE_ARGS += -I$(SRC_DIR)

# Incluir testbench
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# Módulo(s) de prueba cocotb
COCOTB_TEST_MODULES = test

# Reglas de cocotb
include $(shell cocotb-config --makefiles)/Makefile.sim