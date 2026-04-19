# SPDX-FileCopyrightText: © 2026 Bootcamp IEEE OpenSilicon / IEEE CASS UTP
# SPDX-License-Identifier: Apache-2.0

"""
test.py  –  Banco de pruebas cocotb para tt_um_alu7b

Protocolo (17 posedges de captura + 1 posedge S_CALC):

  posedge  1.. 7  → Operando A [6:0], LSB primero, por ui_in[0]
  posedge  8..14  → Operando B [6:0], LSB primero, por ui_in[0]
  posedge 15..17  → Opcode    [2:0], LSB primero, por ui_in[0]
  posedge 18      → FSM S_CALC: Done=1, resultado en uo_out

Sincronía dentro de run_alu:
  reset_dut termina en FallingEdge → ya estamos en semiciclo bajo.
  • bit[0]: poner dato inmediatamente (sin FallingEdge extra) → RisingEdge
  • bit[1..16]: FallingEdge → poner dato → RisingEdge
  Esto garantiza exactamente 17 posedges de captura, sin offset.

Operaciones (op[2:0]):
  000=Suma  001=AND  010=OR  011=XOR  100=Resta
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge

OP_ADD = 0b000
OP_AND = 0b001
OP_OR  = 0b010
OP_XOR = 0b011
OP_SUB = 0b100

CLK_PERIOD_NS = 10   # 100 MHz



# Reset: termina en FallingEdge (semiciclo bajo, listo para enviar bit[0])

async def reset_dut(dut):
    dut.rst_n.value  = 0
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)   # terminar en semiciclo bajo



# Enviar operación serial y capturar resultado

async def run_alu(dut, A, B, op):
    """
    Envía 17 bits seriales LSB-first y devuelve (resultado, done_visto).

    Precondición: llamar inmediatamente después de reset_dut, que deja
    el control en FallingEdge. Así el primer bit se pone sin FallingEdge
    extra, evitando el offset de +1 ciclo.
    """
    bits  = [(A >> i) & 1 for i in range(7)]
    bits += [(B >> i) & 1 for i in range(7)]
    bits += [(op >> i) & 1 for i in range(3)]

    for i, bit in enumerate(bits):
        if i > 0:
            await FallingEdge(dut.clk)   # semiciclo bajo para bits 1..16
        dut.ui_in.value = int(bit)       # dato estable antes del posedge
        await RisingEdge(dut.clk)        # posedge: DUT captura

    # Esperar el posedge de S_CALC (exactamente 1 ciclo después del bit 16)
    dut.ui_in.value = 0
    done_seen  = False
    result_val = 0
    for _ in range(4):
        await FallingEdge(dut.clk)
        await RisingEdge(dut.clk)
        if int(dut.uio_out.value) & 0x01:
            done_seen  = True
            result_val = int(dut.uo_out.value)
            break

    return result_val, done_seen



# test_project  

@cocotb.test()
async def test_project(dut):
    """Prueba completa de la ALU de 7 bits – todas las operaciones."""
    dut._log.info("Start")

    clock = Clock(dut.clk, CLK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset inicial 
    dut._log.info("Reset")
    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)

    dut._log.info("Test project behavior")

    # Tabla de casos (A, B, op, esperado, descripción)
    test_cases = [
        # Suma
        (20,  30,  OP_ADD, (20  + 30)  & 0xFF, "ADD  20 +  30 =  50"),
        (10,  15,  OP_ADD, (10  + 15)  & 0xFF, "ADD  10 +  15 =  25"),
        (100, 100, OP_ADD, (100 + 100) & 0xFF, "ADD 100 + 100 = 200 (carry)"),
        (0,   0,   OP_ADD, 0,                  "ADD   0 +   0 =   0"),
        (127, 1,   OP_ADD, (127 + 1)   & 0xFF, "ADD 127 +   1 = 128"),
        # AND
        (0b1010101, 0b1100110, OP_AND,
         (0b1010101 & 0b1100110) & 0xFF,       "AND 0x55 & 0x66"),
        (0x7F, 0x00, OP_AND, 0x00,             "AND 0x7F & 0x00 = 0x00"),
        (0x7F, 0x7F, OP_AND, 0x7F,             "AND 0x7F & 0x7F = 0x7F"),
        # OR
        (0b0101010, 0b0010101, OP_OR,
         (0b0101010 | 0b0010101) & 0xFF,       "OR  0x2A | 0x15 = 0x3F"),
        (0x00, 0x7F, OP_OR,  0x7F,             "OR  0x00 | 0x7F = 0x7F"),
        # XOR
        (0b1111111, 0b1010101, OP_XOR,
         (0b1111111 ^ 0b1010101) & 0xFF,       "XOR 0x7F ^ 0x55"),
        (0b1100110, 0b1100110, OP_XOR, 0,      "XOR  A  ^  A  =   0"),
        # Resta
        (50,  20,  OP_SUB, (50  - 20)  & 0xFF, "SUB  50 -  20 =  30"),
        (77,  77,  OP_SUB, 0,                  "SUB   A -  A  =   0"),
        (10,  30,  OP_SUB, (10  - 30)  & 0xFF, "SUB  10 -  30  underflow C2"),
    ]

    for idx, (A, B, op, expected, desc) in enumerate(test_cases):
        await reset_dut(dut)
        result, done = await run_alu(dut, A, B, op)

        ok = (result == expected) and done
        dut._log.info(
            f"[{idx+1:02d}] {desc:<35s}  "
            f"got={result:#04x}  exp={expected:#04x}  "
            f"Done={done}  [{'PASS' if ok else 'FAIL'}]"
        )
        assert done, \
            f"[{idx+1}] {desc}: Done nunca se activó"
        assert result == expected, \
            f"[{idx+1}] {desc}: got={result:#04x}, exp={expected:#04x}"

    dut._log.info(f"Todos los {len(test_cases)} casos PASARON correctamente.")