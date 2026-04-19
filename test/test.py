# SPDX-FileCopyrightText: © 2026 Bootcamp IEEE OpenSilicon / IEEE CASS UTP
# SPDX-License-Identifier: Apache-2.0

"""
test.py  –  Banco de pruebas cocotb para tt_um_alu7b
=======================================================

Protocolo de la ALU serial (17 ciclos + 1 ciclo de cálculo):

  Ciclos  1.. 7  →  Operando A [6:0], LSB primero, por ui_in[0]
  Ciclos  8..14  →  Operando B [6:0], LSB primero, por ui_in[0]
  Ciclos 15..17  →  Opcode    [2:0], LSB primero, por ui_in[0]
  Ciclo  18      →  FSM estado S_CALC: Done=1, resultado en uo_out

Operaciones (op[2:0]):
  000 → Suma   001 → AND   010 → OR   011 → XOR   100 → Resta
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

# ---------------------------------------------------------------------------
# Constantes de operación
# ---------------------------------------------------------------------------
OP_ADD = 0b000
OP_AND = 0b001
OP_OR  = 0b010
OP_XOR = 0b011
OP_SUB = 0b100

CLK_PERIOD_NS = 10   # 100 MHz  (bien dentro del límite de 50 MHz del bus TT)
TOTAL_BITS    = 17   # 7 (A) + 7 (B) + 3 (op)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def reset_dut(dut):
    """Reset activo bajo por 5 ciclos."""
    dut.rst_n.value  = 0
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


async def run_alu(dut, A, B, op):
    """
    Envía 17 bits seriales (A 7b, B 7b, op 3b) y espera el resultado.

    La FSM tarda 1 ciclo adicional (S_CALC) tras el bit 17 antes de
    que Done = 1 y el resultado quede en uo_out. La función espera
    hasta Done = 1 (máximo 5 ciclos extra de margen) y devuelve
    (result_int, done_seen).
    """
    # ---- Construir la secuencia de 17 bits (LSB primero) ----
    bits = []
    for i in range(7):
        bits.append((A >> i) & 1)
    for i in range(7):
        bits.append((B >> i) & 1)
    for i in range(3):
        bits.append((op >> i) & 1)

    # ---- Enviar bits seriales ----
    for bit in bits:
        dut.ui_in.value = int(bit)
        await ClockCycles(dut.clk, 1)

    # ---- Esperar Done (máximo 5 ciclos de margen) ----
    # El ciclo S_CALC ocurre 1 flanco después del último bit.
    done_seen  = False
    result_val = 0

    for _ in range(5):
        await RisingEdge(dut.clk)
        if int(dut.uio_out.value) & 0x01:
            done_seen  = True
            result_val = int(dut.uo_out.value)
            break

    return result_val, done_seen


# ===========================================================================
# TEST PRINCIPAL  (reemplaza la plantilla test_project)
# ===========================================================================

@cocotb.test()
async def test_project(dut):
    """Prueba completa de la ALU de 7 bits – todas las operaciones."""
    dut._log.info("Start")

    clock = Clock(dut.clk, CLK_PERIOD_NS, units="ns")
    cocotb.start_soon(clock.start())

    # -----------------------------------------------------------------------
    # Reset inicial
    # -----------------------------------------------------------------------
    dut._log.info("Reset")
    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    dut._log.info("Test project behavior")

    # -----------------------------------------------------------------------
    # Tabla de casos de prueba: (A, B, op, resultado_esperado, descripcion)
    # -----------------------------------------------------------------------
    test_cases = [
        # ── Suma ──────────────────────────────────────────────────────────
        (20,  30,  OP_ADD, (20  + 30)  & 0xFF, "ADD 20+30=50"),
        (10,  15,  OP_ADD, (10  + 15)  & 0xFF, "ADD 10+15=25"),
        (100, 100, OP_ADD, (100 + 100) & 0xFF, "ADD 100+100=200 (carry)"),
        (0,   0,   OP_ADD, 0,                  "ADD 0+0=0"),
        (127, 1,   OP_ADD, (127 + 1)   & 0xFF, "ADD 127+1=128"),
        # ── AND ───────────────────────────────────────────────────────────
        (0b1010101, 0b1100110, OP_AND,
         (0b1010101 & 0b1100110) & 0xFF, "AND 0x55 & 0x66"),
        (0x7F, 0x00, OP_AND, 0,               "AND x & 0 = 0"),
        (0x7F, 0x7F, OP_AND, 0x7F,            "AND x & x = x"),
        # ── OR ────────────────────────────────────────────────────────────
        (0b0101010, 0b0010101, OP_OR,
         (0b0101010 | 0b0010101) & 0xFF, "OR  0x2A | 0x15 = 0x3F"),
        (0x00, 0x7F, OP_OR,  0x7F,            "OR  0 | 0x7F = 0x7F"),
        # ── XOR ───────────────────────────────────────────────────────────
        (0b1111111, 0b1010101, OP_XOR,
         (0b1111111 ^ 0b1010101) & 0xFF, "XOR 0x7F ^ 0x55"),
        (0b1100110, 0b1100110, OP_XOR, 0,     "XOR A^A = 0"),
        # ── Resta ─────────────────────────────────────────────────────────
        (50,  20,  OP_SUB, (50  - 20)  & 0xFF, "SUB 50-20=30"),
        (77,  77,  OP_SUB, 0,                  "SUB A-A=0"),
        (10,  30,  OP_SUB, (10  - 30)  & 0xFF, "SUB 10-30 (underflow C2)"),
    ]

    # -----------------------------------------------------------------------
    # Ejecutar casos
    # -----------------------------------------------------------------------
    for idx, (A, B, op, expected, desc) in enumerate(test_cases):
        await reset_dut(dut)
        result, done = await run_alu(dut, A, B, op)

        status = "PASS" if (result == expected) else "FAIL"
        dut._log.info(
            f"[{idx+1:02d}] {desc:<28s}  "
            f"result={result:#04x}  expected={expected:#04x}  "
            f"Done={done}  [{status}]"
        )

        assert done, \
            f"[{idx+1}] {desc}: señal Done nunca se activó"
        assert result == expected, \
            f"[{idx+1}] {desc}: resultado={result:#04x}, esperado={expected:#04x}"

    dut._log.info(f"Todos los {len(test_cases)} casos pasaron correctamente.")