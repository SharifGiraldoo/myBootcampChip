<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project implements a 7-bit Arithmetic Logic Unit (ALU) for Tiny Tapeout.

The system receives two 7-bit operands serially through a single input pin using LSB-first format.

Input sequence:

1. First 7 clock cycles: Operand A  
2. Next 7 clock cycles: Operand B  
3. After receiving all 14 bits, the ALU executes the selected operation.

Supported operations through control pins `OP2:OP0`:

| OP | Operation |
|----|-----------|
| 000 | A + B |
| 001 | A AND B |
| 010 | A OR B |
| 011 | A XOR B |
| 100 | A - B |

The result appears in parallel on output pins `uo[6:0]`.

When computation finishes, `uo[7]` is asserted as `Done`.

Reset is active low through `rst_n`.

---

## How to test

Use the following pin mapping:

### Inputs

| Pin | Function |
|-----|----------|
| ui[0] | Serial Bit_in |
| ui[1] | OP0 |
| ui[2] | OP1 |
| ui[3] | OP2 |

### Outputs

| Pin | Function |
|-----|----------|
| uo[0]..uo[6] | 7-bit result |
| uo[7] | Done flag |

### Procedure

1. Apply reset (`rst_n = 0`)
2. Release reset (`rst_n = 1`)
3. Set operation code on `ui[3:1]`
4. Send Operand A bit-by-bit (LSB first), one bit per clock cycle
5. Send Operand B bit-by-bit (LSB first), one bit per clock cycle
6. Wait one extra clock cycle
7. Read result on outputs
8. Verify `Done = 1`

### Example

To compute:

20 + 30

- Set OP = `000`
- Send binary 20 LSB first
- Send binary 30 LSB first
- Wait one clock

Expected result:

- Output = 50
- Done = 1

---

## External hardware

No external hardware is required.

Optional hardware for demonstration:

- LEDs connected to outputs
- Push buttons for serial input and clock
- FPGA board or Tiny Tapeout demo board
- Logic analyzer for waveform inspection
