<!---
This file is used to generate your project datasheet. Please fill in the information below and delete any unused sections.
You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

Este proyecto implementa una **Unidad Aritmético-Lógica (ALU) de 7 bits** con interfaz de entrada serial y salida paralela, diseñada para el shuttle **SKY26a (SKY130nm PDK)** en el marco del Bootcamp de Diseño y Fabricación de Chips IEEE OpenSilicon / IEEE CASS UTP 2026.

### Descripción funcional

La ALU recibe dos operandos de 7 bits de forma **serial** (bit a bit, LSB primero) a través del pin `ui_in[0]` (`Bit_in`), junto con un código de operación de 3 bits. Una vez recibidos los 17 bits totales, el resultado aparece en paralelo en `uo_out[7:0]` y la señal `uio_out[0]` (`Done`) se activa durante exactamente un ciclo de reloj para indicar que la operación ha concluido.

### Operaciones soportadas

| `op[2:0]` | Operación | Expresión |
|:---------:|:---------:|:---------:|
| `000`     | Suma      | `A + B`   |
| `001`     | AND       | `A & B`   |
| `010`     | OR        | `A \| B`  |
| `011`     | XOR       | `A ^ B`   |
| `100`     | Resta     | `A - B`   |

### Protocolo de entrada serial

Los datos ingresan **LSB primero** por cada flanco de subida de `clk`, en el siguiente orden:

```
Ciclos  1 ..  7  →  Bits [0..6] del Operando A  (LSB primero)
Ciclos  8 .. 14  →  Bits [0..6] del Operando B  (LSB primero)
Ciclos 15 .. 17  →  Bits [0..2] del Opcode op   (LSB primero)
```

Transcurridos los 17 flancos de reloj, el resultado queda disponible en `uo_out[7:0]` y `Done` (`uio_out[0]`) se activa por un ciclo. Para iniciar una nueva operación es necesario aplicar un pulso de reset activo bajo (`rst_n = 0`).

### Arquitectura interna

El diseño se estructura en dos módulos Verilog:

- **`alu_7b`**: núcleo combinacional que calcula el resultado según el opcode. La salida es de 8 bits: `result[7]` corresponde al carry (suma) o borrow (resta), y `result[6:0]` al resultado de 7 bits.
- **`tt_um_alu7b`**: módulo top-level TinyTapeout que gestiona la recepción serial mediante un contador de 4 bits (`bit_count`) y registros de desplazamiento (`reg_A`, `reg_B`, `reg_op`). Controla además la generación del pulso `Done` y el latcheo del resultado final.

El desplazamiento LSB-first se implementa con inserción por el MSB y corrimiento hacia la derecha:

```verilog
reg_A <= {bit_in, reg_A[6:1]};
```

Esto garantiza que al completarse los 7 ciclos, `reg_A[0]` contiene el LSB y `reg_A[6]` el MSB del operando.

---

## How to test

### Requisitos previos

- Señal de reloj activa en `clk` (frecuencia máxima recomendada: 50 MHz).
- Reset activo bajo (`rst_n`): mantener en `0` hasta que el sistema deba iniciar la recepción de datos.

### Procedimiento paso a paso

1. **Aplicar reset**: llevar `rst_n = 0` por al menos 2 ciclos de reloj y luego `rst_n = 1`.
2. **Enviar el Operando A** (7 bits, LSB primero): en cada ciclo de reloj colocar el bit correspondiente en `ui_in[0]`.
3. **Enviar el Operando B** (7 bits, LSB primero): continuar en los siguientes 7 ciclos de reloj.
4. **Enviar el Opcode** (3 bits, LSB primero): continuar en los siguientes 3 ciclos de reloj.
5. **Leer el resultado**: tras el ciclo 17, observar `uo_out[7:0]`. Cuando `uio_out[0]` (`Done`) se active (nivel alto por 1 ciclo), el resultado es válido.
6. **Nueva operación**: aplicar reset y repetir desde el paso 1.

### Ejemplo: 25 + 38 = 63 (opcode 000)

| Ciclo | Bit enviado | Descripción              |
|:-----:|:-----------:|:-------------------------|
| 1     | 1           | A[0] = 1 (25 = 0011001)  |
| 2     | 0           | A[1] = 0                 |
| 3     | 0           | A[2] = 0                 |
| 4     | 1           | A[3] = 1                 |
| 5     | 1           | A[4] = 1                 |
| 6     | 0           | A[5] = 0                 |
| 7     | 0           | A[6] = 0                 |
| 8     | 0           | B[0] = 0 (38 = 0100110)  |
| 9     | 1           | B[1] = 1                 |
| 10    | 1           | B[2] = 1                 |
| 11    | 0           | B[3] = 0                 |
| 12    | 0           | B[4] = 0                 |
| 13    | 1           | B[5] = 1                 |
| 14    | 0           | B[6] = 0                 |
| 15    | 0           | op[0] = 0 (Suma = 000)   |
| 16    | 0           | op[1] = 0                |
| 17    | 0           | op[2] = 0                |

**Resultado esperado**: `uo_out = 0x3F` (63 decimal), `Done = 1` en el ciclo siguiente.

### Verificación con el banco de pruebas cocotb

El directorio `test/` contiene `test.py` con 8 tests independientes que cubren todas las operaciones, casos de borde (carry, underflow, A=B, AND con cero, XOR consigo mismo) y la señal `Done`. Para ejecutarlos:

```sh
cd test
make -B
```

Para simulación a nivel de compuertas (Gate Level), una vez generado el GDS:

```sh
make -B GATES=yes
```

Para visualizar las formas de onda:

```sh
gtkwave tb.fst tb.gtkw
```

---

## External hardware

Este diseño no requiere hardware externo. Opera exclusivamente con las señales estándar del chip TinyTapeout (reloj, reset, pines de entrada/salida digitales) y puede probarse directamente con el **DevKit** oficial de TinyTapeout sin componentes adicionales.