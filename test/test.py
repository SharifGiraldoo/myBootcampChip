# SPDX-FileCopyrightText: © 2026 Bootcamp IEEE OpenSilicon / IEEE CASS UTP
# SPDX-License-Identifier: Apache-2.0

"""
test.py - Banco de pruebas cocotb para la ALU de 7 bits con entrada serial

Protocolo de entrada serial (17 ciclos de reloj):
  Ciclos  1.. 7 -> Operando A (7 bits, LSB primero)
  Ciclos  8..14 -> Operando B (7 bits, LSB primero)
  Ciclos 15..17 -> Opcode op  (3 bits, LSB primero)

Salida (paralela):
  uo_out[7:0]  -> Resultado (8 bits; bit[7] = carry/borrow)
  uio_out[0]   -> Done (pulso de 1 ciclo de reloj)

Operaciones:
  000 -> Suma
  001 -> AND
  010 -> OR
  011 -> XOR
  100 -> Resta
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge


# ---------------------------------------------------------------------------
# Constantes de operación
# ---------------------------------------------------------------------------
OP_ADD = 0b000  # Suma
OP_AND = 0b001  # AND
OP_OR  = 0b010  # OR
OP_XOR = 0b011  # XOR
OP_SUB = 0b100  # Resta

TOTAL_BITS = 17  # 7 + 7 + 3


# ---------------------------------------------------------------------------
# Función auxiliar: enviar operación serial y obtener resultado
# ---------------------------------------------------------------------------
async def send_alu_operation(dut, A, B, op):
    """
    Envía los 17 bits de la operación de forma serial al DUT.

    Parámetros:
        dut : objeto DUT de cocotb
        A   : int, operando A (0..127)
        B   : int, operando B (0..127)
        op  : int, código de operación (0..7)

    Retorna:
        (result_int, done_seen): resultado leído en uo_out y si Done se detectó
    """
    # Construir la cadena de 17 bits: A[6:0] LSB primero, B[6:0] LSB primero,
    # op[2:0] LSB primero
    bits = []
    for i in range(7):
        bits.append((A >> i) & 1)
    for i in range(7):
        bits.append((B >> i) & 1)
    for i in range(3):
        bits.append((op >> i) & 1)

    done_seen = False
    result_val = 0

    for idx, bit in enumerate(bits):
        # Colocar el bit en ui_in[0] antes del flanco de subida
        dut.ui_in.value = int(bit)
        await ClockCycles(dut.clk, 1)

    # Esperar 2 ciclos adicionales para que el resultado se estabilice
    # y el pulso Done sea visible
    for _ in range(2):
        await RisingEdge(dut.clk)
        if int(dut.uio_out.value) & 0x01:
            done_seen = True
            result_val = int(dut.uo_out.value)

    # Leer resultado final
    if result_val == 0:
        result_val = int(dut.uo_out.value)

    return result_val, done_seen


# ---------------------------------------------------------------------------
# Función auxiliar: reset del DUT
# ---------------------------------------------------------------------------
async def reset_dut(dut):
    """Aplica reset activo bajo por 5 ciclos y libera."""
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


# ===========================================================================
# TEST 1: Verificación de Reset
# ===========================================================================
@cocotb.test()
async def test_reset(dut):
    """Verifica que el reset activo bajo inicializa correctamente el sistema."""
    dut._log.info("=== TEST 1: Reset ===")
    clock = Clock(dut.clk, 10, units="ns")  # 100 MHz
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0

    await ClockCycles(dut.clk, 5)

    # Verificar que la salida es 0 durante reset
    assert int(dut.uo_out.value) == 0, \
        f"uo_out debería ser 0 durante reset, got {int(dut.uo_out.value)}"
    assert (int(dut.uio_out.value) & 0x01) == 0, \
        "Done debería ser 0 durante reset"

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    dut._log.info("Reset verificado correctamente")


# ===========================================================================
# TEST 2: Suma (OP_ADD = 000)
# ===========================================================================
@cocotb.test()
async def test_suma(dut):
    """Verifica la operación de suma de 7 bits."""
    dut._log.info("=== TEST 2: Suma ===")
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    await reset_dut(dut)

    # Caso 1: 10 + 15 = 25
    A, B = 10, 15
    expected = (A + B) & 0xFF
    result, done = await send_alu_operation(dut, A, B, OP_ADD)
    dut._log.info(f"Suma: {A} + {B} = resultado={result}, esperado={expected}, Done={done}")
    assert result == expected, f"FALLO Suma {A}+{B}: esperado={expected}, obtenido={result}"

    await reset_dut(dut)

    # Caso 2: 63 + 64 = 127 (máximo sin carry)
    A, B = 63, 64
    expected = (A + B) & 0xFF
    result, done = await send_alu_operation(dut, A, B, OP_ADD)
    dut._log.info(f"Suma: {A} + {B} = resultado={result}, esperado={expected}")
    assert result == expected, f"FALLO Suma {A}+{B}: esperado={expected}, obtenido={result}"

    await reset_dut(dut)

    # Caso 3: 100 + 100 = 200 (bit de carry en bit[7])
    A, B = 100, 100
    expected = (A + B) & 0xFF  # 200 = 0xC8
    result, done = await send_alu_operation(dut, A, B, OP_ADD)
    dut._log.info(f"Suma con carry: {A} + {B} = resultado={result}, esperado={expected}")
    assert result == expected, f"FALLO Suma con carry {A}+{B}: esperado={expected}, obtenido={result}"

    dut._log.info("Suma verificada correctamente en todos los casos")


# ===========================================================================
# TEST 3: AND (OP_AND = 001)
# ===========================================================================
@cocotb.test()
async def test_and(dut):
    """Verifica la operación AND bit a bit."""
    dut._log.info("=== TEST 3: AND ===")
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    await reset_dut(dut)

    A, B = 0b1010101, 0b1100110  # 85, 102
    expected = (A & B) & 0xFF
    result, done = await send_alu_operation(dut, A, B, OP_AND)
    dut._log.info(f"AND: {A:#09b} & {B:#09b} = {result:#010b}, esperado={expected:#010b}")
    assert result == expected, f"FALLO AND: esperado={expected}, obtenido={result}"

    await reset_dut(dut)

    # AND con 0 -> resultado = 0
    A, B = 0x7F, 0x00
    expected = 0
    result, done = await send_alu_operation(dut, A, B, OP_AND)
    assert result == expected, f"FALLO AND con 0: esperado={expected}, obtenido={result}"

    dut._log.info("AND verificado correctamente")


# ===========================================================================
# TEST 4: OR (OP_OR = 010)
# ===========================================================================
@cocotb.test()
async def test_or(dut):
    """Verifica la operación OR bit a bit."""
    dut._log.info("=== TEST 4: OR ===")
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    await reset_dut(dut)

    A, B = 0b0101010, 0b0010101  # 42, 21 -> OR = 63
    expected = (A | B) & 0xFF
    result, done = await send_alu_operation(dut, A, B, OP_OR)
    dut._log.info(f"OR: {A:#09b} | {B:#09b} = {result:#010b}, esperado={expected:#010b}")
    assert result == expected, f"FALLO OR: esperado={expected}, obtenido={result}"

    await reset_dut(dut)

    # OR con 0x7F -> resultado = 0x7F
    A, B = 0b1010101, 0x7F
    expected = (A | B) & 0xFF
    result, done = await send_alu_operation(dut, A, B, OP_OR)
    assert result == expected, f"FALLO OR con 0x7F: esperado={expected}, obtenido={result}"

    dut._log.info("OR verificado correctamente")


# ===========================================================================
# TEST 5: XOR (OP_XOR = 011)
# ===========================================================================
@cocotb.test()
async def test_xor(dut):
    """Verifica la operación XOR bit a bit."""
    dut._log.info("=== TEST 5: XOR ===")
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    await reset_dut(dut)

    A, B = 0b1111111, 0b1010101  # 127, 85 -> XOR = 42
    expected = (A ^ B) & 0xFF
    result, done = await send_alu_operation(dut, A, B, OP_XOR)
    dut._log.info(f"XOR: {A:#09b} ^ {B:#09b} = {result:#010b}, esperado={expected:#010b}")
    assert result == expected, f"FALLO XOR: esperado={expected}, obtenido={result}"

    await reset_dut(dut)

    # XOR de A consigo mismo -> 0
    A = B = 0b1100110
    expected = 0
    result, done = await send_alu_operation(dut, A, B, OP_XOR)
    assert result == expected, f"FALLO XOR A^A: esperado=0, obtenido={result}"

    dut._log.info("XOR verificado correctamente")


# ===========================================================================
# TEST 6: Resta (OP_SUB = 100)
# ===========================================================================
@cocotb.test()
async def test_resta(dut):
    """Verifica la operación de resta de 7 bits."""
    dut._log.info("=== TEST 6: Resta ===")
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    await reset_dut(dut)

    # Caso 1: 50 - 20 = 30
    A, B = 50, 20
    expected = (A - B) & 0xFF
    result, done = await send_alu_operation(dut, A, B, OP_SUB)
    dut._log.info(f"Resta: {A} - {B} = resultado={result}, esperado={expected}")
    assert result == expected, f"FALLO Resta {A}-{B}: esperado={expected}, obtenido={result}"

    await reset_dut(dut)

    # Caso 2: A = B -> resultado = 0
    A = B = 77
    expected = 0
    result, done = await send_alu_operation(dut, A, B, OP_SUB)
    assert result == expected, f"FALLO Resta A=B: esperado=0, obtenido={result}"

    await reset_dut(dut)

    # Caso 3: A < B -> underflow (complemento a 2 en 8 bits)
    A, B = 10, 30
    expected = (A - B) & 0xFF  # Complemento a 2: 0xEC = 236
    result, done = await send_alu_operation(dut, A, B, OP_SUB)
    dut._log.info(f"Resta underflow: {A} - {B} = resultado={result:#04x}, esperado={expected:#04x}")
    assert result == expected, f"FALLO Resta underflow {A}-{B}: esperado={expected}, obtenido={result}"

    dut._log.info("Resta verificada correctamente")


# ===========================================================================
# TEST 7: Verificación de Done y secuencia completa
# ===========================================================================
@cocotb.test()
async def test_done_signal(dut):
    """Verifica que la señal Done se activa correctamente."""
    dut._log.info("=== TEST 7: Señal Done ===")
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    await reset_dut(dut)

    # Enviar operación y verificar Done
    A, B, op = 7, 5, OP_ADD  # 7 + 5 = 12
    bits = []
    for i in range(7):
        bits.append((A >> i) & 1)
    for i in range(7):
        bits.append((B >> i) & 1)
    for i in range(3):
        bits.append((op >> i) & 1)

    done_cycle = -1
    for idx, bit in enumerate(bits):
        dut.ui_in.value = int(bit)
        await ClockCycles(dut.clk, 1)
        if (int(dut.uio_out.value) & 0x01):
            done_cycle = idx

    # Monitorear ciclos extra para capturar Done
    for extra in range(3):
        await RisingEdge(dut.clk)
        if (int(dut.uio_out.value) & 0x01):
            done_cycle = TOTAL_BITS + extra
            dut._log.info(f"Done detectado en ciclo extra {extra}")

    dut._log.info(f"Done observado en ciclo: {done_cycle}")
    assert done_cycle >= 0, "Done nunca se activó"

    # Verificar resultado
    result = int(dut.uo_out.value)
    assert result == (A + B), f"Resultado con Done incorrecto: esperado={A+B}, obtenido={result}"

    dut._log.info("Señal Done verificada correctamente")


# ===========================================================================
# TEST 8: Múltiples operaciones consecutivas (con reset entre cada una)
# ===========================================================================
@cocotb.test()
async def test_multiples_operaciones(dut):
    """Verifica múltiples operaciones consecutivas con reset entre ellas."""
    dut._log.info("=== TEST 8: Múltiples operaciones ===")
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1

    # Tabla de pruebas: (A, B, op, expected)
    test_cases = [
        (5,   3,   OP_ADD, (5 + 3)   & 0xFF),   # 8
        (127, 1,   OP_ADD, (127 + 1) & 0xFF),   # 128
        (0b1010101, 0b0110011, OP_AND, (0b1010101 & 0b0110011) & 0xFF),
        (0b0001111, 0b1110000, OP_OR,  (0b0001111 | 0b1110000) & 0xFF),
        (0b1111111, 0b0000000, OP_XOR, (0b1111111 ^ 0b0000000) & 0xFF),
        (100, 40,  OP_SUB, (100 - 40) & 0xFF),  # 60
        (20,  50,  OP_SUB, (20 - 50)  & 0xFF),  # Underflow
        (0,   0,   OP_ADD, 0),
        (127, 127, OP_AND, 127),
        (0,   127, OP_OR,  127),
    ]

    passed = 0
    for i, (A, B, op, expected) in enumerate(test_cases):
        await reset_dut(dut)
        result, done = await send_alu_operation(dut, A, B, op)
        op_names = {OP_ADD: "ADD", OP_AND: "AND", OP_OR: "OR",
                    OP_XOR: "XOR", OP_SUB: "SUB"}
        dut._log.info(
            f"Caso {i+1}: {op_names.get(op,'?')}({A},{B}) "
            f"-> resultado={result} (esperado={expected}) "
            f"{'✓ PASS' if result == expected else '✗ FAIL'}"
        )
        assert result == expected, \
            f"FALLO caso {i+1}: {op_names.get(op,'?')}({A},{B}) " \
            f"esperado={expected}, obtenido={result}"
        passed += 1

    dut._log.info(f"Todos los {passed} casos de prueba pasaron exitosamente")