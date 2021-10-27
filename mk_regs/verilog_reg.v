/* Read Only with one shot on read */
module %(MODULE)s_ro1s_reg
  #(
    parameter   RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       RD,          // Write Strobe
    input       DI,          // Data In
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end
      end
   end

endmodule

/* Read/Write */
module %(MODULE)s_rw_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end
      end
   end

endmodule

/* Read/Write, Read Only on control signal */
module %(MODULE)s_rwpr_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      LD,          // Write protect when high
    input      DI,          // Data In
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE & ~LD) begin
            DO <= DI;
         end
      end
   end

endmodule

/* Read/Write, Read Only on control signal */
module %(MODULE)s_rwpr1s_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       LD,          // Write protect when high
    input       DI,          // Data In
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE & ~LD) begin
            DO <= DI;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE & ~LD;
         ws_d <= ws;
      end
   end

endmodule

/* Read/Write with one shot on write */
module %(MODULE)s_rw1s_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule

/* Read/Write with one shot on write */
module %(MODULE)s_rw1s1_reg
  #(
    parameter  RVAL = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule

/* Read/Write with parallel load */
module %(MODULE)s_rwld_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       LD,          // Load Control
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= (LD) ? IN : DO;
         end
      end
   end

endmodule

/* Read/Write with parallel load, with one shot on write */
module %(MODULE)s_rwld1s_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       LD,          // Load Control
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= (LD) ? IN : DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule

/* Read/Write with parallel load, with one shot on write */
module %(MODULE)s_rwld1s1_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       LD,          // Load Control
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= (LD) ? IN : DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule

/* Read/write with input signal that sets bits on one */
module %(MODULE)s_rws_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= IN | DO;
         end
      end
   end

endmodule

/* Read/write with input signal that sets bits on one, one shot on write */
module %(MODULE)s_rws1s_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= IN | DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule

/* Read/write with input signal that sets bits on one, one shot on write of 1 */
module %(MODULE)s_rws1s1_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= IN | DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule

/* Write 1 to clear, bits set on input value */
module %(MODULE)s_w1cs_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE & DI) begin
            DO <= 1'b0;
         end else begin
            DO <= IN | DO;
         end
      end
   end

endmodule

/* Write 1 to clear, bits set on input value, soft clear */
module %(MODULE)s_w1csc_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       LD,          // Soft Clear
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if ((WE & %(BE_LEVEL)sBE & DI) | LD) begin
            DO <= 1'b0;
         end else begin
            DO <= IN | DO;
         end
      end
   end

endmodule

/* Write 1 to clear, bits set on input, one shot on write */
module %(MODULE)s_w1cs1s_reg
  #(
    parameter  RVAL = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE & DI) begin
            DO <= 1'b0;
         end else begin
            DO <= IN | DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule

/* Write 1 to clear, bits set on input, one shot on write */
module %(MODULE)s_w1cs1s1_reg
  #(
    parameter  RVAL = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO[i] <= RVAL[i];
      end else begin
         if (WE & %(BE_LEVEL)sBE & DI[i]) begin
            DO[i] <= 1'b0;
         end else begin
            DO[i] <= IN[i] | DO[i];
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule

/* Write 1 to clear, bits set on load */
module %(MODULE)s_w1cld_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       LD,          // Load Control
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO[i] <= RVAL[i];
      end else begin
         if (WE & %(BE_LEVEL)sBE & DI[i]) begin
            DO[i] <= 1'b0 ;
         end else begin
            DO[i] <= (LD & IN[i]) | DO[i];
         end
      end
   end

endmodule

/* Write 1 to clear, bits set on input, one shot on write */
module %(MODULE)s_w1cld1s_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    input       IN,          // Load Data
    input       LD,          // Load Control
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO[i] <= RVAL[i];
      end else begin
         if (WE & %(BE_LEVEL)sBE & DI[i]) begin
            DO[i] <= 1'b0;
         end else begin
            DO[i] <= (LD & IN[i]) | DO[i];
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule

/* Write 1 to clear, bits set on input, one shot on write */
module %(MODULE)s_w1cld1s1_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    input       IN,          // Load Data
    input       LD,          // Load Control
    output reg  DO,          // Data Out
    output      DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO[i] <= RVAL[i];
      end else begin
         if (WE & %(BE_LEVEL)sBE & DI[i]) begin
            DO[i] <= 1'b0;
         end else begin
            DO[i] <= (LD & IN[i]) | DO[i];
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule

/* Read only, loaded on a control signal */
module %(MODULE)s_rold_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       LD,          // Load Control
    input       IN,          // Load Data
    output reg  DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else if (LD) begin
         DO <= IN;
      end
   end

endmodule

/* Read only, loaded on a control signal, clear on read */
module %(MODULE)s_rcld_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       RD,          // Read Strobe
    input       LD,          // Load Control
    input       IN,          // Load Data
    output reg  DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (LD) begin
            DO <= IN;
         end else begin
            DO <= RD ? 1'b0 : DO;
         end
      end
   end

endmodule

/* Read only, loaded on a control signal, clear on read */
module %(MODULE)s_rv1s_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,  // Clock
    input       %(RST)s, // Reset
    input       RD,   // Read Strobe
    input       IN,   // Load Data
    output      DO,   // Data Out
    output      DO_1S // One shot on read
    );

   reg          ws;
   reg          ws_d;

   assign DO    = IN;
   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= RD;
         ws_d <= ws;
      end
   end

endmodule

/* Read only, bits set on input, clear on read */
module %(MODULE)s_rcs_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       RD,          // Read Strobe
    input       LD,          // Load Control
    input       IN,          // Load Data
    output reg  DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (LD) begin
            DO <= DO | IN;
         end else begin
            DO <= RD ? 1'b0 : DO;
         end
      end
   end

endmodule

module %(MODULE)s_wo_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,     // Clock
    input       %(RST)s,    // Reset
    input       BE,      // Byte Enable
    input       WE,      // Write Strobe
    input       DI,      // Data In
    output      DO       // Data Out
    );

   reg  ws;
   reg  ws_d;

   assign DO = ws & ~ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            ws <= DI;
         end else begin
            ws <= 1'b0;
         end
         ws_d <= ws;
      end
   end

endmodule


module %(MODULE)s_w1s_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,         // Clock
    input       %(RST)s,        // Reset
    input       BE,          // Byte Enable
    input       WE,          // Write Strobe
    input       DI,          // Data In
    input       IN,          // Load Data
    output reg  DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DO | DI;
         end else begin
            DO <= ~(IN) & DO;
         end
      end
   end

endmodule

module %(MODULE)s_w1s1s1_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input      CLK,     // Clock
    input      %(RST)s,    // Reset
    input      BE,      // Byte Enable
    input      WE,      // Write Strobe
    input      DI,      // Data In
    input      IN,      // Load Data
    output reg DO,      // Data Out
    output     DO_1S    // One Shot
    );

   reg         ws;
   reg         ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DO | DI;
         end else begin
            DO <= ~(IN) & DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule

module %(MODULE)s_w1s1s_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input      CLK,  // Clock
    input      %(RST)s, // Reset
    input      BE,   // Byte Enable
    input      WE,   // Write Strobe
    input      DI,   // Data In
    input      IN,   // Load Data
    output reg DO,   // Data Out
    output     DO_1S // One Shot
    );

   reg         ws;
   reg         ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DO | DI;
         end else begin
            DO <= ~(IN) & DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule

/* Read/write with input signal that clears bits on one */
module %(MODULE)s_rwc_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,  // Clock
    input       %(RST)s, // Reset
    input       BE,   // Byte Enable
    input       WE,   // Write Strobe
    input       DI,   // Data In
    input       IN,   // Load Data
    output reg  DO    // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= ~(IN) & DO;
         end
      end
   end

endmodule

/* Read/write with input signal that clears bits on one, one shot on any write */
module %(MODULE)s_rwc1s_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,  // Clock
    input       %(RST)s, // Reset
    input       BE,   // Byte Enable
    input       WE,   // Write Strobe
    input       DI,   // Data In
    input       IN,   // Load Data
    output reg  DO,   // Data Out
    output      DO_1S // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= ~(IN) & DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule

/* Read/write with input signal that clears bits on one, one shot on write of 1 */
module %(MODULE)s_rwc1s1_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,  // Clock
    input       %(RST)s, // Reset
    input       BE,   // Byte Enable
    input       WE,   // Write Strobe
    input       DI,   // Data In
    input       IN,   // Load Data
    output reg  DO,   // Data Out
    output                 DO_1S // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= ~(IN) & DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule

/* Read/write when reset, reset on complement */
module %(MODULE)s_rwrc_reg
  #(
    parameter  RVAL  = 1'b0
    )
   (
    input       CLK,  // Clock
    input       %(RST)s, // Reset
    input       BE,   // Byte Enable
    input       WE,   // Write Strobe
    input       DI,   // Data In
    output reg  DO    // Data Out
    );


   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
        if (WE & %(BE_LEVEL)sBE) begin
           if (DO == RVAL) begin
              DO <= DI;
           end else if (DO == ~DI) begin
              DO <= RVAL;
           end
        end
      end
   end
endmodule
