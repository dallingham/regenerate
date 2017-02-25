# Provide a mapping reserved SystemVerilog keywords to alternatives
# to prevent syntax errors in the generated code.

REMAP_NAME = set(["always", "assign", "automatic", "begin", "case", 
                  "casex", "casez", "class", "do", "package", "set",
                  "cell", "config", "deassign", "default", "defparam",
                  "design", "disable","edge", "else", "end", "endcase",
                  "endconfig", "endfunction", "endgenerate", "endmodule",
                  "endprimitive", "endspecify", "endtable", "endtask",
                  "event", "for", "force", "forever", "fork", "function",
                  "generate", "genvar", "if", "ifnone", "incdir", 
                  "initial", "inout", "input", "instance", "join",
                  "liblist", "library", "localparam", "macromodule",
                  "module", "negedge", "output", "parameter", "posedge",
                  "primitive", "reg", "release", "repeat", "scalared",
                  "signed", "specify", "specparam", "strength", "table",
                  "task", "tri", "tri0", "tri1", "triand", "wand", 
                  "trior", "wor", "trireg", "unsigned", "use", "vectored",
                  "wait", "while", "wire", "bit"]) 
