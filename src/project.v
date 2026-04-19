/*
 * project.v - Punto de entrada del proyecto TinyTapeout
 *
 * Bootcamp Diseño y Fabricación de Chips - UTP 2026
 * Reto: ALU de 7 bits con entrada serial y salida paralela
 *
 * Este archivo simplemente incluye los módulos del diseño.
 * El módulo top-level es tt_um_alu7b definido en tt_um_alu7b.v
 *
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Incluir el módulo núcleo de la ALU
`include "alu_7b.v"

// Incluir el top-level TinyTapeout
`include "tt_um_alu7b.v"