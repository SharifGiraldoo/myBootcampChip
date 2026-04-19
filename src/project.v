/*
 * Copyright (c) 2026 Bootcamp IEEE OpenSilicon / IEEE CASS UTP
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none


// Módulo 1: ALU combinacional de 7 bits
// Op[2:0]:  000=Suma  001=AND  010=OR  011=XOR  100=Resta

module alu_7b (
    input  wire [6:0] A,
    input  wire [6:0] B,
    input  wire [2:0] op,
    output reg  [7:0] result
);
    always @(*) begin
        case (op)
            3'b000: result = {1'b0, A} + {1'b0, B};  // Suma  (bit[7]=carry)
            3'b001: result = {1'b0, A & B};            // AND
            3'b010: result = {1'b0, A | B};            // OR
            3'b011: result = {1'b0, A ^ B};            // XOR
            3'b100: result = {1'b0, A} - {1'b0, B};   // Resta (bit[7]=borrow C2)
            default: result = 8'b0;
        endcase
    end
endmodule


// Módulo 2 (top-level): ALU serial → paralela para TinyTapeout
// Protocolo de entrada serial (ui_in[0] = Bit_in, LSB primero):
//   Flancos  1.. 7  → Operando A [6:0]
//   Flancos  8..14  → Operando B [6:0]
//   Flancos 15..17  → Opcode op  [2:0]
//   Flanco  18      → Done=1, resultado en uo_out[7:0]
// Reset activo bajo (rst_n=0): vuelve al estado inicial.

module tt_um_alu7b (
    input  wire [7:0] ui_in,    // Dedicated inputs  — ui_in[0] = Bit_in
    output wire [7:0] uo_out,   // Dedicated outputs — Data_out[7:0]
    input  wire [7:0] uio_in,   // IOs: Input path   (no usado)
    output wire [7:0] uio_out,  // IOs: Output path  — uio_out[0] = Done
    output wire [7:0] uio_oe,   // IOs: Enable path  (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);


    // Límites de bit_count (0..16, necesita 5 bits)

    localparam [4:0] CNT_A_END  = 5'd6;    // bits 0..6   → reg_A
    localparam [4:0] CNT_B_END  = 5'd13;   // bits 7..13  → reg_B
    localparam [4:0] CNT_OP_END = 5'd16;   // bits 14..16 → reg_op


    // FSM: S_RECV → S_CALC → S_DONE

    localparam [1:0] S_RECV = 2'd0,
                     S_CALC = 2'd1,
                     S_DONE = 2'd2;

    reg [1:0] state;
    reg [4:0] bit_count;
    reg [6:0] reg_A;
    reg [6:0] reg_B;
    reg [2:0] reg_op;
    reg [7:0] reg_result;
    reg       done_reg;

    wire bit_in = ui_in[0];


    // Instancia de la ALU combinacional

    wire [7:0] alu_out;
    alu_7b u_alu (.A(reg_A), .B(reg_B), .op(reg_op), .result(alu_out));


    // FSM + datapath

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= S_RECV;
            bit_count  <= 5'd0;
            reg_A      <= 7'd0;
            reg_B      <= 7'd0;
            reg_op     <= 3'd0;
            reg_result <= 8'd0;
            done_reg   <= 1'b0;
        end else begin
            done_reg <= 1'b0;   // Done es pulso de exactamente 1 ciclo

            case (state)

                S_RECV: begin
                    // Shift-right LSB-first: bit nuevo entra en [MSB], corre a derecha
                    // Tras 7 flancos: reg[6]=MSB ... reg[0]=LSB  → valor correcto
                    if (bit_count <= CNT_A_END)
                        reg_A <= {bit_in, reg_A[6:1]};
                    else if (bit_count <= CNT_B_END)
                        reg_B <= {bit_in, reg_B[6:1]};
                    else
                        reg_op <= {bit_in, reg_op[2:1]};

                    if (bit_count == CNT_OP_END) begin
                        state     <= S_CALC;
                        bit_count <= 5'd0;
                    end else
                        bit_count <= bit_count + 5'd1;
                end

                S_CALC: begin
                    // reg_A/B/op estables - latchar resultado y pulsar Done
                    reg_result <= alu_out;
                    done_reg   <= 1'b1;
                    state      <= S_DONE;
                end

                S_DONE: state <= S_DONE;   // esperar rst_n para nueva operación

                default: state <= S_RECV;
            endcase
        end
    end


    // All output pins must be assigned. If not used, assign to 0.

    assign uo_out  = reg_result;
    assign uio_out = {7'b0, done_reg};
    assign uio_oe  = 8'b0000_0001;   // solo uio[0] es salida (Done)

    // List all unused inputs to prevent warnings
    wire _unused = &{ena, uio_in, ui_in[7:1], 1'b0};

endmodule