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

Level = enum(
    BLOCK=0,
    GROUP=1,
    PROJECT=2
)

BuildCol = enum(
    MODIFIED=0,
    BASE=1,
    FORMAT=2,
    DEST=3,
    CLASS=4,
    DBASE=5,
    TYPE=6
)

MapOpt = enum(
    ID=0,
    CLASS=1,
    REGISTER_SET=2
)

OptMap = enum(
    DESCRIPTION=0,
    CLASS=1,
    REGISTER_SET=2
)

DbMap = enum(
    DBASE=0,
    MODIFIED=1
)

FilterField = enum(
    ADDR=0,
    NAME=1,
    TOKEN=2
)

PrjCol = enum(
    NAME=0,
    ICON=1,
    FILE=2,
    MODIFIED=3,
    OOD=4,
    OBJ=5
)
