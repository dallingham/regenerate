Subsystems
==========

A regenerate project groups register sets into subsystems. Each
subsystem can then contain multiple register sets, and a register set
can appear in more that one subsystem.

What is a subsystem?
--------------------

A subsystem can be thought of as a logic grouping of related logic. In
a typcial SOC today, a design consists of many subsystems. A typical
subsystem might be a CPU subsystem, consisting of a processor,
interrupt controller, UARTs, and other blocks. Each of these blocks
would have their own register sets.

Addressing
----------

Within a subsystem, each register block is located at a offset of the
subsystems address space. Each subsystem as a whole also has an offset
from the relative to its address map.

A register's address is determined by:

  ``Address = AddressMapBase + SubsystemBase + RegisterBase + RegisterAddress``

Repeating Register Sets
-----------------------

Many times, a register set will have multiple occurances within a
subsystem. Frequently, these register sets are located in the address
space at regular offsets within the subsystems address map. Regenerate
allows you to indicate a repeating register set.

A register set within the subsystem has a Repeat Count and Repeat
Offset associated with it. If the repeat count is not equal to 1, then
the register set repeats at the regular interval determined by the
Register Offset.

In this case, a register's address is determined by:

  ``Address = AddressMapBase + SubsystemBase + RegisterBase + (i * RepeatOffset) + RegisterAddress``





