"""
Enums for the Project Prometheus simulation
"""

from enum import Enum

class RoleEnum(str, Enum):
    GUARD = "Guard"
    PRISONER = "Prisoner"

class CellTypeEnum(str, Enum):
    CELL_BLOCK = "Cell_Block"
    CAFETERIA = "Cafeteria"
    YARD = "Yard"
    SOLITARY = "Solitary"
    GUARD_ROOM = "Guard_Room"

class ActionEnum(str, Enum):
    DO_NOTHING = "do_nothing"
    MOVE = "move"
    USE_ITEM = "use_item"
    SPEAK = "speak"
    ATTACK = "attack"

class ItemEnum(str, Enum):
    FOOD = "food"
    WATER = "water"
    BOOK = "book"
    BATON = "baton"