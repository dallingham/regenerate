Parameters
============

Parameters are configuration variables. A default value must be
specified, but parameters may be overridden by the parent project.

Generated RTL code and register packages will also be parameterized.

Where parameters can be used
----------------------------

Parameters may be used to make array dimensions variable. They may
also be used to set the reset values on registers.

Parameter values
----------------

When a parameter is defined, a default value must be specified. This
value will be used, unless overridden by the parent project. By
specifying the Min and Max values, constraints may be placed on the
valid range that the parent project can use.

Notes
-----

* When parameters are used for a dimension, the user must ensure that
  the address space allows for enough space to handle the minimum
  and maximum range values of the parameter.
