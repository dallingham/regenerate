def enum(**enums):
    return type('Enum', (), enums)


BitType = enum(
    READ_ONLY=0,
    READ_ONLY_VALUE=1,
    READ_ONLY_LOAD=2,
    READ_ONLY_CLEAR_LOAD=3,
    READ_ONLY_VALUE_1S=4,
    READ_WRITE=5,
    READ_WRITE_1S=6,
    READ_WRITE_1S_1=7,
    READ_WRITE_LOAD=8,
    READ_WRITE_LOAD_1S=9,
    READ_WRITE_LOAD_1S_1=10,
    READ_WRITE_SET=11,
    READ_WRITE_SET_1S=12,
    READ_WRITE_SET_1S_1=13,
    READ_WRITE_CLR=14,
    READ_WRITE_CLR_1S=15,
    READ_WRITE_CLR_1S_1=16,
    WRITE_1_TO_CLEAR_SET=17,
    WRITE_1_TO_CLEAR_SET_1S=18,
    WRITE_1_TO_CLEAR_SET_1S_1=19,
    WRITE_1_TO_CLEAR_LOAD=20,
    WRITE_1_TO_CLEAR_LOAD_1S=21,
    WRITE_1_TO_CLEAR_LOAD_1S_1=22,
    WRITE_1_TO_SET=23,
    WRITE_1_TO_SET_1S=24,
    WRITE_1_TO_SET_1S1=25,
    WRITE_ONLY=26,
    READ_WRITE_RESET_ON_COMP=27,
    READ_WRITE_PROTECT=28,
    READ_WRITE_PROTECT_1S=29,
    WRITE_1_TO_CLEAR_SET_CLR=30
)

OneShot = enum(
    NONE=0,
    ON_ANY=1,
    ON_ONE=2,
    ON_ZERO=3,
    ON_TOGGLE=4
)

ResetType = enum(
    NUMERIC=0,
    INPUT=1,
    PARAMETER=2
)

InputFunction = enum(
    SET_BITS=0,
    CLEAR_BITS=1,
    PARALLEL=2,
    ASSIGNMENT=3
)

ShareType = enum(
    NONE=0,
    READ=1,
    WRITE=2
)