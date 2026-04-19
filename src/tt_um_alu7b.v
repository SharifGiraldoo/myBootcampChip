/*
 * tt_um_alu7b.v  –  ALU 7 bits, entrada serial, salida paralela
 *
 * Bootcamp Diseño y Fabricación de Chips – IEEE OpenSilicon / IEEE CASS UTP 2026
 *
 * ============================================================
 * PROTOCOLO DE ENTRADA SERIAL  (ui_in[0] = Bit_in)
 * ============================================================
 *
 *  Ciclos  1 ..  7  →  Operando A [6:0], LSB primero
 *  Ciclos  8 .. 14  →  Operando B [6:0], LSB primero
 *  Ciclos 15 .. 17  →  Opcode op  [2:0], LSB primero
 *
 *  Ciclo 18 (S_CALC):  resultado calculado, Done = 1
 *  Ciclo 19+  (S_DONE): resultado estable en uo_out, espera reset
 *
 *  Reset activo bajo (rst_n = 0): vuelve al estado S_RECV.
 *
 * ============================================================
 * MAPA DE PINES TINYTAPEOUT
 * ============================================================
 *
 *  ui_in[0]    → Bit_in  (dato serial)
 *  ui_in[7:1]  → no usados
 *
 *  uo_out[7:0] → Data_out  (resultado; bit[7] = carry/borrow)
 *
 *  uio_out[0]  → Done  (pulso alto 1 ciclo)
 *  uio_out[7:1]→ 0
 *  uio_oe      → 8'b0000_0001
 *
 * ============================================================
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_alu7b (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    // ------------------------------------------------------------------
    // Límites de índice de bits (base 0)
    // ------------------------------------------------------------------
    localparam [3:0] CNT_A_END  = 4'd6;   // bits 0..6   → reg_A
    localparam [3:0] CNT_B_END  = 4'd13;  // bits 7..13  → reg_B
    localparam [3:0] CNT_OP_END = 4'd16;  // bits 14..16 → reg_op

    // ------------------------------------------------------------------
    // Codificación FSM (2 bits)
    // ------------------------------------------------------------------
    localparam [1:0]
        S_RECV = 2'd0,
        S_CALC = 2'd1,
        S_DONE = 2'd2;

    // ------------------------------------------------------------------
    // Registros
    // ------------------------------------------------------------------
    reg [1:0] state;
    reg [3:0] bit_count;

    reg [6:0] reg_A;
    reg [6:0] reg_B;
    reg [2:0] reg_op;

    reg [7:0] reg_result;
    reg       done_reg;

    // ------------------------------------------------------------------
    // Entrada serial
    // ------------------------------------------------------------------
    wire bit_in = ui_in[0];

    // ------------------------------------------------------------------
    // ALU combinacional
    // ------------------------------------------------------------------
    wire [7:0] alu_out;

    alu_7b u_alu (
        .A      (reg_A),
        .B      (reg_B),
        .op     (reg_op),
        .result (alu_out)
    );

    // ------------------------------------------------------------------
    // FSM + datapath
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= S_RECV;
            bit_count  <= 4'd0;
            reg_A      <= 7'd0;
            reg_B      <= 7'd0;
            reg_op     <= 3'd0;
            reg_result <= 8'd0;
            done_reg   <= 1'b0;
        end else begin
            done_reg <= 1'b0;  // done es pulso de 1 ciclo; se limpia cada flanco

            case (state)

                // ---------------------------------------------------
                // S_RECV: shift-register serial, LSB primero
                // ---------------------------------------------------
                S_RECV: begin
                    if (bit_count <= CNT_A_END) begin
                        // Operando A: bit nuevo entra por MSB, shift derecha
                        reg_A <= {bit_in, reg_A[6:1]};
                    end else if (bit_count <= CNT_B_END) begin
                        // Operando B
                        reg_B <= {bit_in, reg_B[6:1]};
                    end else begin
                        // Opcode
                        reg_op <= {bit_in, reg_op[2:1]};
                    end

                    if (bit_count == CNT_OP_END) begin
                        // Último bit recibido → pasar a calcular
                        // reg_op se actualiza en este mismo flanco,
                        // alu_out será válido en el siguiente ciclo (S_CALC)
                        state     <= S_CALC;
                        bit_count <= 4'd0;
                    end else begin
                        bit_count <= bit_count + 4'd1;
                    end
                end

                // ---------------------------------------------------
                // S_CALC: reg_op ya fue registrado, alu_out es estable
                //         → latchar resultado y generar Done
                // ---------------------------------------------------
                S_CALC: begin
                    reg_result <= alu_out;
                    done_reg   <= 1'b1;
                    state      <= S_DONE;
                end

                // ---------------------------------------------------
                // S_DONE: resultado en uo_out; Done ya se limpió
                //         Espera reset para nueva operación
                // ---------------------------------------------------
                S_DONE: begin
                    state <= S_DONE;
                end

                default: state <= S_RECV;

            endcase
        end
    end

    // ------------------------------------------------------------------
    // Asignación de salidas
    // ------------------------------------------------------------------
    assign uo_out  = reg_result;
    assign uio_out = {7'b0, done_reg};
    assign uio_oe  = 8'b0000_0001;

    // Silenciar warnings de entradas no usadas (requerido por Yosys/Verilator)
    wire _unused = &{ena, uio_in, ui_in[7:1], 1'b0};

endmodule