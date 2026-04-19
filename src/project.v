/*
 * project.v - Punto de entrada del proyecto TinyTapeout
 *
 * Bootcamp Diseño y Fabricación de Chips - UTP 2026
 * Reto: ALU de 7 bits con entrada serial y salida paralela
 *
 * NOTA: Los módulos alu_7b y tt_um_alu7b se listan directamente en
 * info.yaml -> source_files y son compilados por LibreLane/Yosys
 * sin necesidad de `include. Este archivo existe para compatibilidad
 * con el Makefile del testbench que referencia PROJECT_SOURCES = project.v,
 * y en ese contexto SÍ usa `include para unir los tres archivos.
 *
 * Para la síntesis GDS (GitHub Actions / tt_tool.py):
 *   info.yaml lista alu_7b.v y tt_um_alu7b.v directamente.
 *
 * Para simulación RTL con cocotb (make en test/):
 *   El Makefile compila project.v que hace `include de los otros dos.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

`include "alu_7b.v"
`include "tt_um_alu7b.v"