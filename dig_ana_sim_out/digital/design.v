// ============================================================
// hc595.v — behavioral model of the 74HC595 8-bit serial-in,
// serial/parallel-out shift register with output latch.
//
// Port names match the KiCad 74xx:74HC595 pin functions so the
// structural netlist builder can wire by pinfunction:
//   SER    pin 14  serial data in
//   SRCLK  pin 11  shift-register clock (rising edge)
//   RCLK   pin 12  storage/latch clock (rising edge)
//   SRCLR_n pin 10 async shift-register clear, active low
//   OE_n   pin 13  output enable, active low (tri-states QA..QH)
//   QA..QH pins 15,1..7  parallel outputs
//   QH_s   pin 9   serial out (QH' — for daisy-chaining)
//
// Chaining: connect one stage's QH_s to the next stage's SER.
// ============================================================
`timescale 1ns/1ps
module hc595 (
    input  wire SER,
    input  wire SRCLK,
    input  wire RCLK,
    input  wire SRCLR_n,
    input  wire OE_n,
    output wire QA, QB, QC, QD, QE, QF, QG, QH,
    output wire QH_s
);
    reg [7:0] shift;   // shift register
    reg [7:0] latch;   // storage register

    // Shift register: sample SER on rising SRCLK; async clear.
    always @(posedge SRCLK or negedge SRCLR_n) begin
        if (!SRCLR_n)
            shift <= 8'b0;
        else
            shift <= {shift[6:0], SER};
    end

    // Storage register latches the shift register on rising RCLK.
    always @(posedge RCLK)
        latch <= shift;

    // Parallel outputs, tri-stated when OE_n is high.
    assign {QH, QG, QF, QE, QD, QC, QB, QA} = OE_n ? 8'bz : latch;

    // Serial output is the MSB of the shift register (daisy-chain).
    assign QH_s = shift[7];
endmodule


module analog_NN_digital (
    input  RCLK,
    input  SRCLK,
    input  ser,
    output CS11,
    output CS11_h,
    output CS11_neg,
    output CS11_neg_h,
    output CS12,
    output CS12_h,
    output CS12_neg,
    output CS12_neg_h,
    output CS13,
    output CS13_h,
    output CS13_neg,
    output CS13_neg_h,
    output CS14_h,
    output CS14_neg_h,
    output CS21,
    output CS21_h,
    output CS21_neg,
    output CS21_neg_h,
    output CS22,
    output CS22_h,
    output CS22_neg,
    output CS22_neg_h,
    output CS23,
    output CS23_h,
    output CS23_neg,
    output CS23_neg_h,
    output CS24_h,
    output CS24_neg_h,
    output CS31,
    output CS31_h,
    output CS31_neg,
    output CS31_neg_h,
    output CS32,
    output CS32_h,
    output CS32_neg,
    output CS32_neg_h,
    output CS33,
    output CS33_h,
    output CS33_neg,
    output CS33_neg_h,
    output CS34_h,
    output CS34_neg_h,
    output CS41,
    output CS41_h,
    output CS41_neg,
    output CS41_neg_h,
    output CS42,
    output CS42_h,
    output CS42_neg,
    output CS42_neg_h,
    output CS43,
    output CS43_h,
    output CS43_neg,
    output CS43_neg_h,
    output CS44_h,
    output CS44_neg_h,
    output Wo1,
    output Wo1_neg,
    output Wo2,
    output Wo2_neg,
    output Wo3,
    output Wo3_neg,
    output Wo4,
    output Wo4_neg,
    output unconnected__U39_QH__Pad9_
);
    wire GND = 1'b0;
    wire VCC = 1'b1;
    wire Net__U36_QH__;
    wire Net__U36_SER_;
    wire Net__U37_QH__;
    wire Net__U38_QH__;
    wire Net__U93_QH__;
    wire Net__U94_QH__;
    wire Net__U95_QH__;

    hc595 U36 ( .SER(Net__U36_SER_), .SRCLK(SRCLK), .RCLK(RCLK), .SRCLR_n(VCC), .OE_n(GND), .QA(CS11_neg), .QB(CS21_neg), .QC(CS31_neg), .QD(CS41_neg), .QE(CS12_neg), .QF(CS22_neg), .QG(CS32_neg), .QH(CS42_neg), .QH_s(Net__U36_QH__) );
    hc595 U37 ( .SER(Net__U36_QH__), .SRCLK(SRCLK), .RCLK(RCLK), .SRCLR_n(VCC), .OE_n(GND), .QA(CS13_neg), .QB(CS23_neg), .QC(CS33_neg), .QD(CS43_neg), .QE(CS11_neg_h), .QF(CS21_neg_h), .QG(CS31_neg_h), .QH(CS41_neg_h), .QH_s(Net__U37_QH__) );
    hc595 U38 ( .SER(Net__U37_QH__), .SRCLK(SRCLK), .RCLK(RCLK), .SRCLR_n(VCC), .OE_n(GND), .QA(CS12_neg_h), .QB(CS22_neg_h), .QC(CS32_neg_h), .QD(CS42_neg_h), .QE(CS13_neg_h), .QF(CS23_neg_h), .QG(CS33_neg_h), .QH(CS43_neg_h), .QH_s(Net__U38_QH__) );
    hc595 U39 ( .SER(Net__U38_QH__), .SRCLK(SRCLK), .RCLK(RCLK), .SRCLR_n(VCC), .OE_n(GND), .QA(CS14_neg_h), .QB(CS24_neg_h), .QC(CS34_neg_h), .QD(CS44_neg_h), .QE(Wo1_neg), .QF(Wo2_neg), .QG(Wo3_neg), .QH(Wo4_neg), .QH_s(unconnected__U39_QH__Pad9_) );
    hc595 U93 ( .SER(ser), .SRCLK(SRCLK), .RCLK(RCLK), .SRCLR_n(VCC), .OE_n(GND), .QA(CS11), .QB(CS21), .QC(CS31), .QD(CS41), .QE(CS12), .QF(CS22), .QG(CS32), .QH(CS42), .QH_s(Net__U93_QH__) );
    hc595 U94 ( .SER(Net__U93_QH__), .SRCLK(SRCLK), .RCLK(RCLK), .SRCLR_n(VCC), .OE_n(GND), .QA(CS13), .QB(CS23), .QC(CS33), .QD(CS43), .QE(CS11_h), .QF(CS21_h), .QG(CS31_h), .QH(CS41_h), .QH_s(Net__U94_QH__) );
    hc595 U95 ( .SER(Net__U94_QH__), .SRCLK(SRCLK), .RCLK(RCLK), .SRCLR_n(VCC), .OE_n(GND), .QA(CS12_h), .QB(CS22_h), .QC(CS32_h), .QD(CS42_h), .QE(CS13_h), .QF(CS23_h), .QG(CS33_h), .QH(CS43_h), .QH_s(Net__U95_QH__) );
    hc595 U96 ( .SER(Net__U95_QH__), .SRCLK(SRCLK), .RCLK(RCLK), .SRCLR_n(VCC), .OE_n(GND), .QA(CS14_h), .QB(CS24_h), .QC(CS34_h), .QD(CS44_h), .QE(Wo1), .QF(Wo2), .QG(Wo3), .QH(Wo4), .QH_s(Net__U36_SER_) );
endmodule // analog_NN_digital
