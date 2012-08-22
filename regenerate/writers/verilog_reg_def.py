REG = {
    "rw" : """module %(MODULE)s_rw_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO        // Data Out
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= DO;
         end
      end
   end

endmodule
""",
    "rw1s" : """module %(MODULE)s_rw1s_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO,       // Data Out
    output reg             DO_1S     // One Shot
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
         DO_1S <= 1'b0;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
            DO_1S <= 1'b1;
         end else begin
            DO <= DO;
            DO_1S <= 1'b0;
         end
      end
   end

endmodule
""",
    "rw1s1" : """module %(MODULE)s_rw1s1_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO,       // Data Out
    output reg             DO_1S     // One Shot
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= DO;
         end
      end
   end

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO_1S <= 1'b0;
      end else begin
         DO_1S <= WE & %(BE_LEVEL)sBE && DI != {pWidth{1'b0}};
      end
   end

endmodule
""",
    "rwld" : """module %(MODULE)s_rwld_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input                  LD,       // Load Control
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO        // Data Out
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
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
""",
    "rwld1s" : """module %(MODULE)s_rwld1s_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input                  LD,       // Load Control
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO,       // Data Out
    output reg             DO_1S     // One Shot
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
         DO_1S <= 1'b0;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
            DO_1S <= 1'b1;
         end else begin
            DO <= (LD) ? IN : DO;
            DO_1S <= 1'b0;
         end
      end
   end

endmodule
""",
    "rwld1s1" : """module %(MODULE)s_rwld1s1_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input                  LD,       // Load Control
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO,       // Data Out
    output reg             DO_1S     // One Shot
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end else begin
            DO <= (LD) ? IN : DO;
         end
      end
   end

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO_1S <= 1'b0;
      end else begin
         DO_1S <= WE && %(BE_LEVEL)sBE && DI != {pWidth{1'b0}};
      end
   end

endmodule
""",
    "rws" : """module %(MODULE)s_rws_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO        // Data Out
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
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
""",
    "rws1s" : """module %(MODULE)s_rws1s_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO,       // Data Out
    output reg             DO_1S     // One Shot
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
         DO_1S <= 1'b0;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
            DO_1S <= 1'b1;
         end else begin
            DO <= IN | DO;
            DO_1S <= 1'b0;
         end
      end
   end

endmodule
""",
    "w1cs" : """module %(MODULE)s_w1cs_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO        // Data Out
    );

   genvar                  i;
   generate
      for(i = 0; i < WIDTH; i = i + 1) begin
         always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
            if (%(RESET_CONDITION)sRSTn) begin
               DO[i] <= RVAL[i];
            end else begin
               if (WE & %(BE_LEVEL)sBE & DI[i]) begin
                  DO[i] <= 1'b0;
               end else begin
                  DO[i] <= IN[i] | DO[i];
               end
            end
         end
      end
   endgenerate

endmodule
""",
    "w1cs1s" : """module %(MODULE)s_w1cs1s_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO,       // Data Out
    output reg             DO_1S     // One Shot
    );

   genvar                  i;
   generate
      for(i = 0; i < WIDTH; i = i + 1) begin
         always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
            if (%(RESET_CONDITION)sRSTn) begin
               DO[i] <= RVAL[i];
            end else begin
               if (WE & %(BE_LEVEL)sBE & DI[i]) begin
                  DO[i] <= 1'b0;
               end else begin
                  DO[i] <= IN[i] | DO[i];
               end
            end
         end
      end
   endgenerate

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO_1S <= 1'b0;
      end else begin
         DO_1S <= WE & %(BE_LEVEL)sBE;
      end
   end

endmodule
""",
    "w1cs1s1" : """module %(MODULE)s_w1cs1s1_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO,       // Data Out
    output reg             DO_1S     // One Shot
    );

   genvar                  i;
   generate
      for(i = 0; i < WIDTH; i = i + 1) begin
         always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
            if (%(RESET_CONDITION)sRSTn) begin
               DO[i] <= RVAL[i];
            end else begin
               if (WE & %(BE_LEVEL)sBE & DI[i]) begin
                  DO[i] <= 1'b0;
               end else begin
                  DO[i] <= IN[i] | DO[i];
               end
            end
         end
      end
   endgenerate

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO_1S <= 1'b0;
      end else begin
         DO_1S <= WE && %(BE_LEVEL)sBE && DI != {pWidth{1'b0}};
      end
   end

endmodule
""",
    "w1cld" : """module %(MODULE)s_w1cld_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input                  LD,       // Load Control
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO        // Data Out
    );

   genvar                  i;
   generate
      for(i = 0; i < WIDTH; i = i + 1) begin
         always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
            if (%(RESET_CONDITION)sRSTn) begin
               DO[i] <= RVAL[i];
            end else begin
               if (WE & %(BE_LEVEL)sBE & DI[i]) begin
                  DO[i] <= 1'b0 ;
               end else begin
                  DO[i] <= (LD & IN[i]) | DO[i];
               end
            end
         end
      end
   endgenerate

endmodule
""",
    "w1cld1s" : """module %(MODULE)s_w1cld1s_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  BE,       // Byte Enable
    input                  WE,       // Write Strobe
    input [WIDTH-1:0]      DI,       // Data In
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO,       // Data Out
    output reg             DO_1S     // One Shot
    );

   genvar                  i;
   generate
      for(i = 0; i < WIDTH; i = i + 1) begin
         always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
            if (%(RESET_CONDITION)sRSTn) begin
               DO[i] <= RVAL[i];
            end else begin
               if (WE & %(BE_LEVEL)sBE & DI[i]) begin
                  DO[i] <= 1'b0;
               end else begin
                  DO[i] <= (LD & IN[i]) | DO[i];
               end
            end
         end
      end
   endgenerate

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO_1S <= 1'b0;
      end else begin
         DO_1S <= WE & %(BE_LEVEL)sBE;
      end
   end

endmodule
""",
    "rold" : """module %(MODULE)s_rold_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  LD,       // Load Control
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO        // Data Out
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
      end else begin
         DO <= (LD) ? IN : DO;
      end
   end

endmodule
""",
    "rcld" : """module %(MODULE)s_rcld_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  RD,       // Read Strobe
    input                  LD,       // Load Control
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO        // Data Out
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
      end else begin
         if (LD) begin
            DO <= IN;
         end else begin
            DO <= RD ? (WIDTH(1'b0)) : DO;
         end
      end
   end

endmodule
""",
    "rcs" : """module %(MODULE)s_rcs_reg #(parameter WIDTH = 1)
   (
    input                  CLK,      // Clock
    input                  RSTn,     // Reset
    input                  RD,       // Read Strobe
    input                  LD,       // Load Control
    input [WIDTH-1:0]      IN,       // Load Data
    input [WIDTH-1:0]      RVAL,     // Reset Value
    output reg [WIDTH-1:0] DO        // Data Out
   );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
      end else begin
         if (LD) begin
            DO <= DO | IN;
         end else begin
            DO <= RD ? (WIDTH(1'b0)) : DO;
         end
      end
   end

endmodule
""",
    "wo" : """module %(MODULE)s_wo_reg
   (
    input      CLK,      // Clock
    input      RSTn,     // Reset
    input      BE,       // Byte Enable
    input      WE,       // Write Strobe
    input      DI,       // Data In
    input      RVAL,     // Reset Value
    output reg DO_1S     // One Shot
    );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO_1S <= RVAL;
      end else begin
         DO_1S <= WE & %(BE_LEVEL)sBE & DI;
      end
   end

endmodule
""",
    "w1s" : """module %(MODULE)s_w1s_reg
   (
    input      CLK,      // Clock
    input      RSTn,     // Reset
    input      BE,       // Byte Enable
    input      WE,       // Write Strobe
    input      DI,       // Data In
    input      RVAL,     // Reset Value
    input      IN,       // Load Data
    output reg DO,       // Data Out
    output reg DO_1S     // One Shot
    );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
         DO_1S <= 1'b0;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DO | DI;
            DO_1S <= 1'b1;
         end else begin
            DO <= ~(IN) & DO;
            DO_1S <= 1'b0;
         end
      end
   end

endmodule
""",
 }
