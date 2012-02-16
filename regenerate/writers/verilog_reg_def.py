REG = {
    "rw" : """module %s_rw_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO
   );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO <= RVAL;
      end else begin
         if (WE & BE) begin
            DO <= DI;
         end else begin
            DO <= DO;
         end
      end
   end

endmodule
""",
    "rw1s" : """module %s_rw1s_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO,
    output reg             DO_1S
   );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO <= RVAL;
         DO_1S <= 1'b0;
      end else begin
         if (WE & BE) begin
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
    "rwld" : """module %s_rwld_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input                  LD,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO
   );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
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
    "rwld1s" : """module %s_rwld1s_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input                  LD,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO,
    output reg             DO_1S
   );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO <= RVAL;
         DO_1S <= 1'b0;
      end else begin
         if (WE & BE) begin
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
    "rwld1s1" : """module %s_rwld1s1_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input                  LD,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO,
    output reg             DO_1S
   );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO <= RVAL;
         DO_1S <= 1'b0;
      end else begin
         if (WE & BE) begin
            DO <= DI;
            DO_1S <= DI;
         end else begin
            DO <= (LD) ? IN : DO;
            DO_1S <= 1'b0;
         end
      end
   end

endmodule
""",
    "rws" : """module %s_rws_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO
   );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
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
    "rws1s" : """module %s_rws1s_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO,
    output reg             DO_1S
   );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO <= RVAL;
         DO_1S <= 1'b0;
      end else begin
         if (WE & BE) begin
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
    "w1cs" : """module %s_w1cs_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO
    );

   genvar                  i;
   generate
      for(i = 0; i < WIDTH; i = i + 1) begin
         always @(posedge CLK or negedge RSTn) begin
            if (~RSTn) begin
               DO[i] <= RVAL[i];
            end else begin
               if (WE & BE & DI[i]) begin
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
    "w1cs1s" : """module %s_w1cs1s_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO,
    output reg             DO_1S
    );

   genvar                  i;
   generate
      for(i = 0; i < WIDTH; i = i + 1) begin
         always @(posedge CLK or negedge RSTn) begin
            if (~RSTn) begin
               DO[i] <= RVAL[i];
            end else begin
               if (WE & BE & DI[i]) begin
                  DO[i] <= 1'b0;
               end else begin
                  DO[i] <= IN[i] | DO[i];
               end
            end
         end
      end
   endgenerate

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO_1S <= 1'b0;
      end else begin
         DO_1S <= WE & BE;
      end
   end

endmodule
""",
    "w1cs1s1" : """module %s_w1cs1s1_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO,
    output reg             DO_1S
    );

   genvar                  i;
   generate
      for(i = 0; i < WIDTH; i = i + 1) begin
         always @(posedge CLK or negedge RSTn) begin
            if (~RSTn) begin
               DO[i] <= RVAL[i];
            end else begin
               if (WE & BE & DI[i]) begin
                  DO[i] <= 1'b0;
               end else begin
                  DO[i] <= IN[i] | DO[i];
               end
            end
         end
      end
   endgenerate

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO_1S <= 1'b0;
      end else begin
         DO_1S <= WE & BE & (|(DI));
      end
   end

endmodule
""",
    "w1cld" : """module %s_w1cld_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input                  LD,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO
    );

   genvar                  i;
   generate
      for(i = 0; i < WIDTH; i = i + 1) begin
         always @(posedge CLK or negedge RSTn) begin
            if (~RSTn) begin
               DO[i] <= RVAL[i];
            end else begin
               if (WE & BE & DI[i]) begin
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
    "w1cld1s" : """module %s_w1cld1s_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  BE,
    input                  WE,
    input [WIDTH-1:0]      DI,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO,
    output reg             DO_1S
    );

   genvar                  i;
   generate
      for(i = 0; i < WIDTH; i = i + 1) begin
         always @(posedge CLK or negedge RSTn) begin
            if (~RSTn) begin
               DO[i] <= RVAL[i];
            end else begin
               if (WE & BE & DI[i]) begin
                  DO[i] <= 1'b0;
               end else begin
                  DO[i] <= (LD & IN[i]) | DO[i];
               end
            end
         end
      end
   endgenerate

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO_1S <= 1'b0;
      end else begin
         DO_1S <= WE & BE;
      end
   end

endmodule
""",
    "rold" : """module %s_rold_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  LD,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO
   );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO <= RVAL;
      end else begin
         DO <= (LD) ? IN : DO;
      end
   end

endmodule
""",
    "rcld" : """module %s_rcld_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  RD,
    input                  LD,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO
   );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
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
    "rcs" : """module %s_rcs_reg #(parameter WIDTH = 1)
   (
    input                  CLK,
    input                  RSTn,
    input                  RD,
    input                  LD,
    input [WIDTH-1:0]      IN,
    input [WIDTH-1:0]      RVAL,
    output reg [WIDTH-1:0] DO
   );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO <= RVAL;
      end else begin
         if (LD) begin
            DO <= DO | IN;
         end else begin
            DO <= RD ? {WIDTH{1'b0}} : DO;
         end
      end
   end

endmodule
""",
    "wo" : """module %s_wo_reg
   (
    input      CLK,
    input      RSTn,
    input      BE,
    input      WE,
    input      DI,
    input      RVAL,
    output reg DO_1S
    );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO_1S <= RVAL;
      end else begin
         DO_1S <= WE & BE & DI;
      end
   end

endmodule
""",
    "w1s" : """module %s_w1s_reg
   (
    input      CLK,
    input      RSTn,
    input      BE,
    input      WE,
    input      DI,
    input      RVAL,
    input      IN,
    output reg DO,
    output reg DO_1S
    );

   always @(posedge CLK or negedge RSTn) begin
      if (~RSTn) begin
         DO <= RVAL;
         DO_1S <= 1'b0;
      end else begin
         if (WE & BE) begin
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
