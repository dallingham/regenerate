Regenerate
==========

.. sectnum::

Creating a project
------------------

Regenerate is project based. A project consists of multiple register
sets, along with the relationships between them. These relationships
include:

* Logical groupings of registers along with their associated
  addressing.
* Address maps

Creating a New Register Set
***************************

Adding an Existing Register Set
*******************************

Creating a Subsystem
********************

Adding a Register Set to a Subsystem
************************************

Defining Address Maps
*********************

Defining Registers
------------------

Address Fields
**************

Each register has an address associated with it. The register is a
register set is not an absolute address, but rather an address offset
from the begining of the register set. The address must be aligned to
the register width.

Memory regions mapped to register space can be also be represented. In
the case, the address used is in the format of:

  ``Address:NumberOfBytes``

Regenerate will not generate code for memory regions.

Name
****

The Name is a descriptive name of the register. This is typically a
phrase, and can consist of multiple words.

Token
*****

The Token is a symbolic name for the register. It is used in creating
define names and variable names in generated code. This should be a
single word, consisting of ASCII letters (typically capital letters),
numbers, and underscores.

Width
*****

The width of the register specifies the number of bits in the
register. The number of bits must be either 8, 16, 32, or 64. The
width must be aligned correctly with the address. For example, and
32-bit address can be ``0x1000`` and ``0x1004``, but cannot be
``0x1001``, ``0x1002``, or ``0x1003``.

Defining Bit Fields
-------------------

More to come...

Using the Builder
-----------------

More to come...
