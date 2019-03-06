def enum(**enums):
    return type('Enum', (), enums)


InstCol = enum(
    INST=0,
    ID=1,
    BASE=2,
    SORT=3,
    RPT=4,
    OFF=5,
    HDL=6,
    UVM=7,
    DEC=8,
    ARRAY=9,
    SINGLE_DEC=10,
    OBJ=11
)

AddrCol = enum(
    NAME=0,
    BASE=1,
    FIXED=2,
    UVM=3,
    WIDTH=4,
    ACCESS=5
)

BitCol = enum(
    ICON=0,
    BIT=1,
    NAME=2,
    TYPE=3,
    RESET=4,
    RESET_TYPE=5,
    SORT=6,
    FIELD=7
)
