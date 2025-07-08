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
    # Basic Actions
    DO_NOTHING = "do_nothing"
    MOVE = "move"
    USE_ITEM = "use_item"
    GIVE_ITEM = "give_item"            # 给予物品
    SPEAK = "speak"
    ATTACK = "attack"
    
    # Guard-specific Actions
    ANNOUNCE_RULE = "announce_rule"          # 制定规则广播
    PATROL_INSPECT = "patrol_inspect"        # 巡逻检查
    ENFORCE_PUNISHMENT = "enforce_punishment" # 执行惩罚
    ASSIGN_TASK = "assign_task"             # 分配任务
    EMERGENCY_ASSEMBLY = "emergency_assembly" # 紧急集合
    
    # Prisoner-specific Actions
    STEAL_ITEM = "steal_item"               # 偷取物品
    FORM_ALLIANCE = "form_alliance"         # 组织联盟
    DIG_TUNNEL = "dig_tunnel"               # 挖掘地道
    CRAFT_WEAPON = "craft_weapon"           # 制作武器
    SPREAD_RUMOR = "spread_rumor"           # 散布谣言

class ItemEnum(str, Enum):
    # Basic Items
    FOOD = "food"
    WATER = "water"
    BOOK = "book"
    
    # Guard Equipment
    BATON = "baton"                  # 警棍
    HANDCUFFS = "handcuffs"         # 手铐
    RADIO = "radio"                 # 对讲机
    KEYS = "keys"                   # 钥匙
    FIRST_AID = "first_aid"         # 急救包
    WHISTLE = "whistle"             # 哨子
    
    # Prisoner Items
    CIGARETTES = "cigarettes"       # 香烟
    PLAYING_CARDS = "playing_cards" # 扑克牌
    DIARY = "diary"                 # 日记本
    SPOON = "spoon"                 # 铁勺
    BEDSHEET = "bedsheet"           # 床单
    SOAP = "soap"                   # 肥皂
    
    # Craftable/Environmental Items
    SHIV = "shiv"                   # 简易刀具
    ROPE = "rope"                   # 绳子
    LOCKPICK = "lockpick"           # 撬锁工具
    TOOLBOX = "toolbox"             # 工具箱
    CHAIR = "chair"                 # 椅子
    TABLE = "table"                 # 桌子