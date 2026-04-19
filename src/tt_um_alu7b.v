/*
 * tt_um_alu7b.v  –  ALU 7 bits, entrada serial, salida paralela
 * Bootcamp Diseño y Fabricación de Chips – IEEE OpenSilicon / IEEE CASS UTP 2026
 *
 * PROTOCOLO SERIAL (ui_in[0] = Bit_in):
 *   Flancos  1.. 7  → Operando A [6:0], LSB primero
 *   Flancos  8..14  → Operando B [6:0], LSB primero
 *   Flancos 15..17  → Opcode    [2:0], LSB primero
 *   Flanco  18      → S_CALC: Done=1, resultado en uo_out
 *
 * Shift-register LSB-first correcto = shift-RIGHT, bit nuevo en MSB:
 *   reg_A  <= {bit_in, reg_A[6:1]}
 *   reg_B  <= {bit_in, reg_B[6:1]}
 *   reg_op <= {bit_in, reg_op[2:1]}
 *   Tras N flancos el valor completo está en reg[N-1:0] con [0]=LSB.
 *
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
    // Límites de bit_count (base 0).  Máximo = 16 → necesita 5 bits.
    // ------------------------------------------------------------------
    localparam [4:0] CNT_A_END  = 5'd6;    // bits 0..6   → reg_A
    localparam [4:0] CNT_B_END  = 5'd13;   // bits 7..13  → reg_B
    localparam [4:0] CNT_OP_END = 5'd16;   // bits 14..16 → reg_op

    // ------------------------------------------------------------------
    // FSM
    // ------------------------------------------------------------------
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

    // ------------------------------------------------------------------
    // ALU combinacional
    // ------------------------------------------------------------------
    wire [7:0] alu_out;
    alu_7b u_alu (.A(reg_A), .B(reg_B), .op(reg_op), .result(alu_out));

    // ------------------------------------------------------------------
    // FSM + datapath
    // ------------------------------------------------------------------
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
            done_reg <= 1'b0;   // pulso de 1 ciclo: se limpia cada flanco

            case (state)

                // ----------------------------------------------------------
                // S_RECV: captura serial con shift-right LSB-first
                //   bit nuevo entra en MSB y se desplaza hacia LSB
                //   Tras 7 flancos: reg[6]=MSB ... reg[0]=LSB  ✓
                // ----------------------------------------------------------
                S_RECV: begin
                    if (bit_count <= CNT_A_END) begin
                        reg_A <= {bit_in, reg_A[6:1]};
                    end else if (bit_count <= CNT_B_END) begin
                        reg_B <= {bit_in, reg_B[6:1]};
                    end else begin
                        reg_op <= {bit_in, reg_op[2:1]};
                    end

                    if (bit_count == CNT_OP_END) begin
                        // Último bit (índice 16) recibido.
                        // reg_A, reg_B, reg_op quedan estables en este flanco.
                        // El siguiente ciclo (S_CALC) la ALU ya los ve correctos.
                        state     <= S_CALC;
                        bit_count <= 5'd0;
                    end else begin
                        bit_count <= bit_count + 5'd1;
                    end
                end

                // ----------------------------------------------------------
                // S_CALC: reg_A/B/op estables → latchar resultado y pulsar Done
                // ----------------------------------------------------------
                S_CALC: begin
                    reg_result <= alu_out;
                    done_reg   <= 1'b1;
                    state      <= S_DONE;
                end

                // ----------------------------------------------------------
                // S_DONE: resultado en uo_out, Done ya se limpió.
                //         Esperar rst_n para nueva operación.
                // ----------------------------------------------------------
                S_DONE: begin
                    state <= S_DONE;
                end

                default: state <= S_RECV;
            endcase
        end
    end

    // ------------------------------------------------------------------
    // Salidas
    // ------------------------------------------------------------------
    assign uo_out  = reg_result;
    assign uio_out = {7'b0, done_reg};
    assign uio_oe  = 8'b0000_0001;

    wire _unused = &{ena, uio_in, ui_in[7:1], 1'b0};

endmodule