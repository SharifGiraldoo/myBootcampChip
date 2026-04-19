/*
 * tt_um_alu7b.v - Top-level TinyTapeout: ALU de 7 bits con entrada serial
 *
 * Bootcamp Diseño y Fabricación de Chips - UTP 2026
 * Autor: Bootcamp IEEE OpenSilicon / IEEE CASS UTP
 *
 * ============================================================
 * DESCRIPCIÓN DEL PROTOCOLO DE COMUNICACIÓN SERIAL
 * ============================================================
 *
 * La ALU recibe 17 bits en total de manera SERIAL por el pin ui_in[0] (Bit_in):
 *
 *   Ciclos  1..7  -> Bits [0..6] del Operando A (LSB primero)
 *   Ciclos  8..14 -> Bits [0..6] del Operando B (LSB primero)
 *   Ciclos 15..17 -> Bits [0..2] del Opcode op   (LSB primero)
 *
 * Tras recibir los 17 bits, el resultado aparece en uo_out[7:0]
 * y uio_out[0] (Done) se activa por exactamente 1 ciclo de reloj.
 *
 * Reset activo bajo (/RST = rst_n): cuando rst_n = 0, el sistema
 * regresa al estado inicial (bit_count = 0, Done = 0).
 *
 * ============================================================
 * MAPA DE PINES TinyTapeout
 * ============================================================
 *
 * ui_in[0]  -> Bit_in  (dato serial de entrada)
 * ui_in[1]  -> (no usado)
 * ...
 * ui_in[7]  -> (no usado)
 *
 * uo_out[7:0] -> Data_out[7:0] (resultado en paralelo, 8 bits)
 *                  bit [7] = carry/borrow para suma/resta
 *                  bits[6:0] = resultado de 7 bits
 *
 * uio_out[0]  -> Done  (pulso alto 1 ciclo cuando operación terminó)
 * uio_out[7:1]-> 0 (no usados)
 * uio_oe[0]   -> 1 (Done es salida)
 * uio_oe[7:1] -> 0
 *
 * ============================================================
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_alu7b (
    input  wire [7:0] ui_in,    // Entradas dedicadas: ui_in[0] = Bit_in
    output wire [7:0] uo_out,   // Salidas dedicadas:  Data_out[7:0]
    input  wire [7:0] uio_in,   // IOs: camino de entrada (no usados)
    output wire [7:0] uio_out,  // IOs: camino de salida: uio_out[0] = Done
    output wire [7:0] uio_oe,   // IOs: habilitación de salida
    input  wire       ena,      // Habilitación del diseño (siempre 1)
    input  wire       clk,      // Reloj
    input  wire       rst_n     // Reset activo bajo
);

    // -------------------------------------------------------
    // Parámetros de la máquina de estados / conteo de bits
    // -------------------------------------------------------
    // Total de bits seriales a recibir:
    //   7 bits operando A + 7 bits operando B + 3 bits op = 17 bits
    localparam TOTAL_BITS   = 17;
    localparam BITS_OP_A    = 7;
    localparam BITS_OP_B    = 7;
    localparam BITS_OPCODE  = 3;

    // -------------------------------------------------------
    // Registros internos
    // -------------------------------------------------------
    reg [3:0]  bit_count;   // Contador de bits recibidos (0..16 = 17 niveles)
    reg [6:0]  reg_A;       // Registro de desplazamiento para operando A
    reg [6:0]  reg_B;       // Registro de desplazamiento para operando B
    reg [2:0]  reg_op;      // Registro de desplazamiento para opcode
    reg [7:0]  reg_result;  // Registro de resultado (salida latched)
    reg        done_reg;    // Bandera de Done (1 ciclo)

    // -------------------------------------------------------
    // Señal Bit_in (entrada serial)
    // -------------------------------------------------------
    wire bit_in = ui_in[0];

    // -------------------------------------------------------
    // Instancia de la ALU combinacional
    // -------------------------------------------------------
    wire [7:0] alu_result;

    alu_7b u_alu (
        .A      (reg_A),
        .B      (reg_B),
        .op     (reg_op),
        .result (alu_result)
    );

    // -------------------------------------------------------
    // Lógica secuencial: captura serial y control de estado
    // -------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset: volver al estado inicial
            bit_count  <= 4'd0;
            reg_A      <= 7'd0;
            reg_B      <= 7'd0;
            reg_op     <= 3'd0;
            reg_result <= 8'd0;
            done_reg   <= 1'b0;
        end else begin
            // Pulso de Done dura exactamente 1 ciclo
            done_reg <= 1'b0;

            if (bit_count < TOTAL_BITS) begin
                // ---- Fase de captura serial ----

                if (bit_count < BITS_OP_A) begin
                    // Bits 0..6 -> Operando A (LSB primero, shift izquierda)
                    reg_A <= {bit_in, reg_A[6:1]};
                end else if (bit_count < (BITS_OP_A + BITS_OP_B)) begin
                    // Bits 7..13 -> Operando B (LSB primero, shift izquierda)
                    reg_B <= {bit_in, reg_B[6:1]};
                end else begin
                    // Bits 14..16 -> Opcode (LSB primero, shift izquierda)
                    reg_op <= {bit_in, reg_op[2:1]};
                end

                bit_count <= bit_count + 4'd1;

                // En el último bit (bit 16) se activa el resultado
                if (bit_count == (TOTAL_BITS - 1)) begin
                    // El opcode completo estará disponible combinacionalmente
                    // en el siguiente ciclo; por ello registramos el resultado
                    // usando la última porción del opcode incluida ahora.
                    // Nota: el opcode se finaliza en este flanco, así que
                    // calculamos el resultado en el siguiente always (ver abajo).
                    done_reg <= 1'b1;
                end
            end else begin
                // Operación completada. Esperar reset para nueva operación.
                // bit_count se queda en TOTAL_BITS hasta reset.
                done_reg <= 1'b0;
            end
        end
    end

    // -------------------------------------------------------
    // Captura del resultado: se registra cuando bit_count == TOTAL_BITS
    // Esto ocurre el ciclo SIGUIENTE al último bit (done_reg se puso en 1),
    // por lo que el resultado ya es estable con el opcode completo.
    // -------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reg_result <= 8'd0;
        end else begin
            if (bit_count == TOTAL_BITS) begin
                reg_result <= alu_result;
            end
        end
    end

    // -------------------------------------------------------
    // Asignaciones de salida
    // -------------------------------------------------------
    assign uo_out   = reg_result;     // Resultado de 8 bits en paralelo
    assign uio_out  = {7'b0, done_reg}; // bit 0 = Done
    assign uio_oe   = 8'b0000_0001;   // Solo uio[0] es salida (Done)

    // -------------------------------------------------------
    // Entradas no usadas: conexión para evitar warnings de síntesis
    // -------------------------------------------------------
    wire _unused = &{ena, uio_in, ui_in[7:1], 1'b0};

endmodule