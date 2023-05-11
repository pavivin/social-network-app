from enum import Enum


def count_max_length(enum: Enum):
    return max((len(val) for val in enum))
