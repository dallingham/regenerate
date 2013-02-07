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

ID Format Control
-----------------

When regenerate creates ID tokens for a register, it may not create
them in format that may be desired. By default, the ID token is
created using the subsystem name and register name. The ID format
field allows the user to override this format. Text, combined with a
few special formatting tokens, gives the user higher control.

The special formatting tokens are:

``%{G}s``
  subsystem name in upper case
``%{g}s``
  subsystem name in lower case
``%{S}s``
  register set name in upper case
``%{s}s``
  register set name in lower case
``%{d}s``
  array index (if repeat count is greater than one), or an empty string if 
  the repeat count is one.
``%{R}s``
  register name in upper case
``%{r}s``
  register name in lower case

The default format is "``%{G}s%{d}s_%{R}s``".



