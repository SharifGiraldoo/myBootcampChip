/*
 * alu_7b.v - Unidad Aritmético-Lógica de 7 bits
 * 
 * Bootcamp Diseño y Fabricación de Chips - UTP 2026
 * Reto: ALU de 7 bits con entrada serial y salida paralela
 *
 * Operaciones soportadas (codificación op[2:0]):
 *   000 -> Suma   : result = A + B
 *   001 -> AND    : result = A & B
 *   010 -> OR     : result = A | B
 *   011 -> XOR    : result = A ^ B
 *   100 -> Resta  : result = A - B
 *
 * Entradas:
 *   A   [6:0] - Operando A (7 bits)
 *   B   [6:0] - Operando B (7 bits)
 *   op  [2:0] - Código de operación
 *
 * Salidas:
 *   result [7:0] - Resultado (8 bits para acomodar carry/borrow en suma/resta)
 *
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module alu_7b (
    input  wire [6:0] A,       // Operando A
    input  wire [6:0] B,       // Operando B
    input  wire [2:0] op,      // Código de operación
    output reg  [7:0] result   // Resultado de 8 bits
);

    // Lógica combinacional: selección de operación
    always @(*) begin
        case (op)
            3'b000: result = {1'b0, A} + {1'b0, B};  // Suma  (bit [7] = carry)
            3'b001: result = {1'b0, A & B};            // AND
            3'b010: result = {1'b0, A | B};            // OR
            3'b011: result = {1'b0, A ^ B};            // XOR
            3'b100: result = {1'b0, A} - {1'b0, B};   // Resta (complemento a 2)
            default: result = 8'b0;                    // Operación no definida
        endcase
    end

endmodule