REG = {
    "ro1s": """module %(MODULE)s_ro1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      RD,          // Write Strobe
    input      DI,          // Data In
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
            DO <= DI;
         end
      end
   end

endmodule
""",
    "rw": """module %(MODULE)s_rw_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
            DO <= DI;
         end
      end
   end

endmodule
""",
    "rwpr": """module %(MODULE)s_rwpr_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
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
         if (WE & BE & ~LD) begin
            DO <= DI;
         end
      end
   end

endmodule
""",
    "rwpr1s": """module %(MODULE)s_rwpr1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      LD,          // Write protect when high
    input      DI,          // Data In
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE & ~LD) begin
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
         ws <= WE & BE & ~LD;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rw1s": """module %(MODULE)s_rw1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
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
         ws <= WE & BE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rw1s1": """module %(MODULE)s_rw1s1_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
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
         ws <= WE & BE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rwld": """module %(MODULE)s_rwld_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      LD,          // Load Control
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
            DO <= DI;
         end else begin
            DO <= (LD) ? IN : DO;
         end
      end
   end

endmodule
""",
    "rwld1s": """module %(MODULE)s_rwld1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      LD,          // Load Control
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg         ws;
   reg         ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
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
         ws <= WE & BE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rwld1s1": """module %(MODULE)s_rwld1s1_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      LD,          // Load Control
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
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
         ws <= WE & BE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rws": """module %(MODULE)s_rws_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
            DO <= DI;
         end else begin
            DO <= IN | DO;
         end
      end
   end

endmodule
""",
    "rws1s": """module %(MODULE)s_rws1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg         ws;
   reg         ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
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
         ws <= WE & BE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rws1s1": """module %(MODULE)s_rws1s1_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
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
         ws <= WE & BE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1cs": """module %(MODULE)s_w1cs_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE & DI) begin
            DO <= IN;
         end else begin
            DO <= IN | DO;
         end
      end
   end

endmodule
""",
    "w1csc": """module %(MODULE)s_w1csc_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      LD,          // Soft Clear
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if ((WE & BE & DI) | LD) begin
            DO <= 1'b0;
         end else begin
            DO <= IN | DO;
         end
      end
   end

endmodule
""",
    "w1cs1s": """module %(MODULE)s_w1cs1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg         ws;
   reg         ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE & DI) begin
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
         ws <= WE & BE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1cs1s1": """module %(MODULE)s_w1cs1s1_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE & DI) begin
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
         ws <= WE & BE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1cld": """module %(MODULE)s_w1cld_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      LD,          // Load Control
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE & DI) begin
            DO <= 1'b0 ;
         end else begin
            DO <= (LD & IN) | DO;
         end
      end
   end

endmodule
""",
    "w1cld1s": """module %(MODULE)s_w1cld1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    input      LD,          // Load Control
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE & DI) begin
            DO <= 1'b0;
         end else begin
            DO <= (LD & IN) | DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & BE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1cld1s1": """module %(MODULE)s_w1cld1s1_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    input      LD,          // Load Control
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE & DI) begin
            DO <= 1'b0;
         end else begin
            DO <= (LD & IN) | DO;
         end
      end
   end

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & BE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rold": """module %(MODULE)s_rold_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      LD,          // Load Control
    input      IN,          // Load Data
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else if (LD) begin
         DO <= IN;
      end
   end

endmodule
""",
    "rcld": """module %(MODULE)s_rcld_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      RD,          // Read Strobe
    input      LD,          // Load Control
    input      IN,          // Load Data
    output reg DO           // Data Out
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
""",
    "rv1s": """module %(MODULE)s_rv1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      RD,          // Read Strobe
    input      IN,          // Load Data
    output     DO,          // Data Out
    output     DO_1S        // One shot on read
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
""",
    "rcs": """module %(MODULE)s_rcs_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      RD,          // Read Strobe
    input      LD,          // Load Control
    input      IN,          // Load Data
    output reg DO           // Data Out
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
""",
    "wo": """module %(MODULE)s_wo_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    output     DO           // Data Out
    );

   reg  ws;
   reg  ws_d;

   assign DO = ws & ~ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         if (WE & BE) begin
            ws <= DI;
         end else begin
            ws <= 1'b0;
         end
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1s": """module %(MODULE)s_w1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
            DO <= DO | DI;
         end else begin
            DO <= ~(IN) & DO;
         end
      end
   end

endmodule
""",
    "w1s1s1": """module %(MODULE)s_w1s1s1_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg         ws;
   reg         ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
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
         ws <= WE & BE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1s1s": """module %(MODULE)s_w1s1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg         ws;
   reg         ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
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
         ws <= WE & BE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rwc": """module %(MODULE)s_rwc_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO           // Data Out
    );

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
            DO <= DI;
         end else begin
            DO <= ~(IN) & DO;
         end
      end
   end

endmodule
""",
    "rwc1s": """module %(MODULE)s_rwc1s_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg          ws;
   reg          ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
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
         ws <= WE & BE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rwc1s1": """module %(MODULE)s_rwc1s1_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    input      IN,          // Load Data
    output reg DO,          // Data Out
    output     DO_1S        // One Shot
    );

   reg         ws;
   reg         ws_d;

   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
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
         ws <= WE & BE && DI != 1'b0;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rwrc": """module %(MODULE)s_rwrc_reg
   (
    input      CLK,         // Clock
    input      %(RST)s,        // Reset
    input      RVAL,        // Value on reset
    input      BE,          // Byte Enable
    input      WE,          // Write Strobe
    input      DI,          // Data In
    output reg DO           // Data Out
    );


   always @(posedge CLK%(RESET_TRIGGER)s) begin
      if (%(RESET_CONDITION)s%(RST)s) begin
         DO <= RVAL;
      end else begin
        if (WE & BE) begin
           if (DO == RVAL) begin
              DO <= DI;
           end else if (DO == ~DI) begin
              DO <= RVAL;
           end
        end
      end
   end
endmodule
""",
 }
