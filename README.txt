Regenerate is a system for maintaining registers in a VLSI design. The
program allows you to specify the functionality of the registers. The
data is stored in an XML database. Once the registers have been
defined, regenerate can create:

* Synthesizable Verilog RTL code of the registers
* Documenation
* Tests
* UVM (Universal Verification Methodology) register definitions
* Header files for C and assembly code

Why is it called "regenerate?"

* It "generates" registers. A common shorthand for register is "reg", 
  so "reg generate".
* This is the third time I've written a program like this for similar
  purposes. So, like the Doctor, when the program dies, it just
  regenerates into a different form. This verison is Open Source, so
  hopefully it will live on.
