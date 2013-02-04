Address Maps
============

In many designs, the same register can be accessed through various
different means. For example, your system may have an external CPU in
addition to an internal CPU. Each of these CPUs may access the
register using different addresses.

Regenerate allows you to specify different address maps, each with its
own base address. Each register's address is derived by adding the
base address value to the register's address.

The address may be either fixed, or relocatable. If the address is not
fixed, then the address is determined at run time. An example of this
would be on a PCIe port, where all addresses are relative to a run
time assigned Base Address Register. On other systems, for example, an
embedded CPU, the address map may be hard coded. The register map is
always fixed at the same location, select the "Fixed Address" option.

If the address is not fixed, then regenerate will use the specified
Base Address field for examples, but will generate all files with the
address as being relocatable.
