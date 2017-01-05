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

Address Maps and Subsystems
---------------------------

Each address map must contain at least one of the subsytems listed in
the Subsystems list. This indicates that the subsystem's registers are
visible in the address map. All registers in all blocks in the
subsystem are visible in the address map. Partial blocks are not
supported.

Adding a Subsystem to an Address Map
------------------------------------

Selecting an address map in the Address Maps list and clicking on the
Edit button next to the list will bring up a dialog allowing you to
select which subsystems belong to the address map. This button will
only be visible when a address map is selected in the list. Selecting
components underneath address map will disable the Edit button.

Clicking the button will bring up a dialog that lists all available
subsystems. Check each subsystem that should belong to the address
map.


   
