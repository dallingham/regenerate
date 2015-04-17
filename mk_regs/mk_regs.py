#! /usr/bin/env python
import sys


def build_file(infile, outfile):

    try:
        f = open(infile)
    except IOError, msg:
        sys.stderr("Could not open input file '%s' : %s\n", infile, msg)
        sys.exit(1)

    try:
        o = open(outfile, "w")
    except IOError, msg:
        sys.stderr("Could not open output file '%s' : %s\n", outfile, msg)
        sys.exit(1)

    in_module = False
    current_text = []

    o.write("REG = {\n")

    current_mod = None
    for line in f.readlines():
        if in_module:
            current_text.append(line)
            if line.startswith("endmodule"):
                in_module = False
                o.write('    "%s" : """%s""",\n' %
                        (current_mod, "".join(current_text)))
        elif line.startswith("module"):
            in_module = True
            current_mod = line.split()[1].split("_")[1]
            current_text = [line]

    o.write(" }\n")
    f.close()
    o.close()


build_file("verilog_reg.v", "verilog_reg_def.py")
