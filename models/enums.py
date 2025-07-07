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
    PICKUP_ITEM = "pickup_item"
    DROP_ITEM = "drop_item"
    USE_ITEM = "use_item"
    SPEAK = "speak"
    ATTACK = "attack"
    REPORT_TO_WARDEN = "report_to_warden"
    TRIGGER_EVENT = "trigger_event"

class ItemEnum(str, Enum):
    FOOD = "food"
    WATER = "water"
    BOOK = "book"
    BATON = "baton"