REG = {
    "ro1s" : """module %(MODULE)s_ro1s_reg #(
                           parameter WIDTH = 1,
                           parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                           )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  RD,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end
      end
   end

endmodule
""",
    "rw" : """module %(MODULE)s_rw_reg #(
                           parameter WIDTH = 1,
                           parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                           )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    output reg [WIDTH-1:0] DO           // Data Out
    );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
      end else begin
         if (WE & %(BE_LEVEL)sBE) begin
            DO <= DI;
         end
      end
   end

endmodule
""",
    "rw1s" : """module %(MODULE)s_rw1s_reg #(
                             parameter WIDTH = 1,
                             parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                             )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   reg                     ws;
   reg                     ws_d;

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

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rw1s1" : """module %(MODULE)s_rw1s1_reg #(
                              parameter WIDTH = 1,
                              parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                              )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   reg                     ws;
   reg                     ws_d;

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

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != {WIDTH{1'b0}};
         ws_d <= ws;
      end
   end

endmodule
""",
    "rwld" : """module %(MODULE)s_rwld_reg #(
                             parameter WIDTH = 1,
                             parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                             )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input                  LD,          // Load Control
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO           // Data Out
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
    "rwld1s" : """module %(MODULE)s_rwld1s_reg #(
                               parameter WIDTH = 1,
                               parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                               )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input                  LD,          // Load Control
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   reg                     ws;
   reg                     ws_d;

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

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rwld1s1" : """module %(MODULE)s_rwld1s1_reg #(
                                parameter WIDTH = 1,
                                parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                                )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input                  LD,          // Load Control
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   reg                     ws;
   reg                     ws_d;

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

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != {WIDTH{1'b0}};
         ws_d <= ws;
      end
   end

endmodule
""",
    "rws" : """module %(MODULE)s_rws_reg #(
                            parameter WIDTH = 1,
                            parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                            )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO           // Data Out
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
    "rws1s" : """module %(MODULE)s_rws1s_reg #(
                              parameter WIDTH = 1,
                              parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                              )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   reg                     ws;
   reg                     ws_d;

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

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rws1s1" : """module %(MODULE)s_rws1s1_reg #(
                               parameter WIDTH = 1,
                               parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                               )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   reg                     ws;
   reg                     ws_d;

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

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != {WIDTH{1'b0}};
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1cs" : """module %(MODULE)s_w1cs_reg #(
                             parameter WIDTH = 1,
                             parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                             )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO           // Data Out
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
    "w1cs1s" : """module %(MODULE)s_w1cs1s_reg #(
                               parameter WIDTH = 1,
                               parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                               )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   reg                     ws;
   reg                     ws_d;

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

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1cs1s1" : """module %(MODULE)s_w1cs1s1_reg #(
                                parameter WIDTH = 1,
                                parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                                )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   reg                     ws;
   reg                     ws_d;

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

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != {WIDTH{1'b0}};
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1cld" : """module %(MODULE)s_w1cld_reg #(
                              parameter WIDTH = 1,
                              parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                              )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input                  LD,          // Load Control
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO           // Data Out
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
    "w1cld1s" : """module %(MODULE)s_w1cld1s_reg #(
                                parameter WIDTH = 1,
                                parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                                )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    input                  LD,          // Load Control
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   reg                     ws;
   reg                     ws_d;

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

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1cld1s1" : """module %(MODULE)s_w1cld1s1_reg #(
                                 parameter WIDTH = 1,
                                 parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                                 )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    input                  LD,          // Load Control
    output reg [WIDTH-1:0] DO,          // Data Out
    output                 DO_1S        // One Shot
    );

   reg                     ws;
   reg                     ws_d;

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

   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != {WIDTH{1'b0}};
         ws_d <= ws;
      end
   end

endmodule
""",
    "rold" : """module %(MODULE)s_rold_reg #(
                             parameter WIDTH = 1,
                             parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                             )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  LD,          // Load Control
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO           // Data Out
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
    "rcld" : """module %(MODULE)s_rcld_reg #(
                             parameter WIDTH = 1,
                             parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                             )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  RD,          // Read Strobe
    input                  LD,          // Load Control
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO           // Data Out
    );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         DO <= RVAL;
      end else begin
         if (LD) begin
            DO <= IN;
         end else begin
            DO <= RD ? {WIDTH{1'b0}} : DO;
         end
      end
   end

endmodule
""",
    "rv1s" : """module %(MODULE)s_rv1s_reg #(
                             parameter WIDTH = 1,
                             parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                             )
   (
    input              CLK,  // Clock
    input              RSTn, // Reset
    input              RD,   // Read Strobe
    input [WIDTH-1:0]  IN,   // Load Data
    output [WIDTH-1:0] DO,   // Data Out
    output             DO_1S // One shot on read
    );

   reg                 ws;
   reg                 ws_d;

   assign DO    = IN;
   assign DO_1S = ws & !ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= RD;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rcs" : """module %(MODULE)s_rcs_reg #(
                            parameter WIDTH = 1,
                            parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                            )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  RD,          // Read Strobe
    input                  LD,          // Load Control
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO           // Data Out
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
    "wo" : """module %(MODULE)s_wo_reg #(
                           parameter WIDTH = 1,
                           parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                           )
   (
    input  CLK,                 // Clock
    input  RSTn,                // Reset
    input  BE,                  // Byte Enable
    input  WE,                  // Write Strobe
    input  [WIDTH-1:0] DI,      // Data In
    output DO,                  // Data Out
    output DO_1S                // One Shot
    );

   reg     ws;
   reg     ws_d;

   assign DO_1S = ws & !ws_d;
   assign DO = 1'b0;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != {WIDTH{1'b0}};
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1s" : """module %(MODULE)s_w1s_reg #(
                            parameter WIDTH = 1,
                            parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                            )
   (
    input                  CLK,         // Clock
    input                  RSTn,        // Reset
    input                  BE,          // Byte Enable
    input                  WE,          // Write Strobe
    input [WIDTH-1:0]      DI,          // Data In
    input [WIDTH-1:0]      IN,          // Load Data
    output reg [WIDTH-1:0] DO           // Data Out
    );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
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
""",
    "w1s1s1" : """module %(MODULE)s_w1s1s1_reg #(
                               parameter WIDTH = 1,
                               parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                               )
   (
    input      CLK,     // Clock
    input      RSTn,    // Reset
    input      BE,      // Byte Enable
    input      WE,      // Write Strobe
    input      DI,      // Data In
    input      IN,      // Load Data
    output reg DO,      // Data Out
    output     DO_1S    // One Shot
    );

   reg         ws;
   reg         ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
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

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != {WIDTH{1'b0}};
         ws_d <= ws;
      end
   end

endmodule
""",
    "w1s1s" : """module %(MODULE)s_w1s1s_reg #(
                              parameter WIDTH = 1,
                              parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                              )
   (
    input      CLK,  // Clock
    input      RSTn, // Reset
    input      BE,   // Byte Enable
    input      WE,   // Write Strobe
    input      DI,   // Data In
    input      IN,   // Load Data
    output reg DO,   // Data Out
    output     DO_1S // One Shot
    );

   reg         ws;
   reg         ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
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

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rwc" : """module %(MODULE)s_rwc_reg #(
                            parameter WIDTH = 1,
                            parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                            )
   (
    input                  CLK,  // Clock
    input                  RSTn, // Reset
    input                  BE,   // Byte Enable
    input                  WE,   // Write Strobe
    input [WIDTH-1:0]      DI,   // Data In
    input [WIDTH-1:0]      IN,   // Load Data
    output reg [WIDTH-1:0] DO    // Data Out
    );

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
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
""",
    "rwc1s" : """module %(MODULE)s_rwc1s_reg #(
                              parameter WIDTH = 1,
                              parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                              )
   (
    input                  CLK,  // Clock
    input                  RSTn, // Reset
    input                  BE,   // Byte Enable
    input                  WE,   // Write Strobe
    input [WIDTH-1:0]      DI,   // Data In
    input [WIDTH-1:0]      IN,   // Load Data
    output reg [WIDTH-1:0] DO,   // Data Out
    output                 DO_1S // One Shot
    );

   reg                     ws;
   reg                     ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
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

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE;
         ws_d <= ws;
      end
   end

endmodule
""",
    "rwc1s1" : """module %(MODULE)s_rwc1s1_reg #(
                               parameter WIDTH = 1,
                               parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                               )
   (
    input                  CLK,  // Clock
    input                  RSTn, // Reset
    input                  BE,   // Byte Enable
    input                  WE,   // Write Strobe
    input [WIDTH-1:0]      DI,   // Data In
    input [WIDTH-1:0]      IN,   // Load Data
    output reg [WIDTH-1:0] DO,   // Data Out
    output                 DO_1S // One Shot
    );

   reg                     ws;
   reg                     ws_d;

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
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

   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
         ws <= 1'b0;
         ws_d <= 1'b0;
      end else begin
         ws <= WE & %(BE_LEVEL)sBE && DI != {WIDTH{1'b0}};
         ws_d <= ws;
      end
   end

endmodule
""",
    "rwrc" : """module %(MODULE)s_rwrc_reg #(
                             parameter WIDTH = 1,
                             parameter [WIDTH-1:0] RVAL = {(WIDTH){1'b0}}
                             )
   (
    input                  CLK,  // Clock
    input                  RSTn, // Reset
    input                  BE,   // Byte Enable
    input                  WE,   // Write Strobe
    input [WIDTH-1:0]      DI,   // Data In
    output reg [WIDTH-1:0] DO    // Data Out
    );


   always @(posedge CLK or %(RESET_EDGE)s RSTn) begin
      if (%(RESET_CONDITION)sRSTn) begin
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
""",
 }
