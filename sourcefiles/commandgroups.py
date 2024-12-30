from enum import Enum


class EventCommandType(Enum):
    ANIMATION = "Animation"
    ASSIGNMENT = "Assignment"
    BATTLE = "Battle"
    BIT_MATH = "Bit Math"
    BYTE_MATH = "Byte Math"
    CHANGE_LOCATION = "Change Location"
    CHECK_BUTTON = "Check Button"
    CHECK_INVENTORY = "Check Inventory"
    CHECK_PARTY = "Check Party"
    CHECK_RESULT = "Check Result"
    CHECK_STORYLINE = "Check Storyline"
    COMPARISON = "Comparison"
    END = "End"
    FACING = "Facing"
    GOTO = "Goto"
    HP_MP = "HP/MP"
    INVENTORY = "Inventory"
    MEM_COPY = "Memory Copy"
    MODE7 = "Mode7"
    OBJECT_COORDINATES = "Object Coordinates"
    OBJECT_FUNCTION = "Object Function"
    PALETTE = "Palette"
    PAUSE = "Pause"
    PARTY_MANAGEMENT = "Party Management"
    RANDOM_NUM = "Random Number"
    SCENE_MANIP = "Scene Manipulation"
    SOUND = "Sound"
    SPRITE_COLLISION = "Sprite Collision"
    SPRITE_DRAWING = "Sprite Drawing"
    SPRITE_MOVEMENT = "Sprite Movement"
    TEXT = "Text"
    UNKNOWN = "Unknown"

class AnimationCommandType(Enum):
    ANIMATION = "Animation"
    ANIMATION_LIMITER = "Animation Limiter"
    RESET_ANIMATION = "Reset Animation"

class AssignmentCommandType(Enum):
    GET_PC1 = "Get PC1"
    GET_STORYLINE = "Get Storyline"
    MEM_TO_MEM = "Mem to Mem"
    RESULT = "Result"
    SET_STORYLINE = "Set Storyline"
    VALUE_TO_MEM = "Value To Mem"

class BattleCommandType(Enum):
    BATTLE = "Battle"

class BitMathCommandType(Enum):
    BIT_MATH = "Bit Math"
    DOWNSHIFT = "Downshift"
    SET_AT = "Set Bits at 7E0154"

class ByteMathCommandType(Enum):
    MEM_TO_MEM = "Mem to Mem"
    VAL_TO_MEM = "Value to Mem"

class ChangeLocationCommandType(Enum):
    CHANGE_LOCATION = "Change Location"
    CHANGE_LOCATION_FROM_MEM = "Change Location from Mem"

class CheckButtonCommandType(Enum):
    CHECK_BUTTON = "Check Button"

class CheckPartyCommandType(Enum):
    CHECK_PARTY = "Check Party"

class CheckResultCommandType(Enum):
    CHECK_RESULT = "Check Result"

class CheckStorylineCommandType(Enum):
    CHECK_STORYLINE = "Check Storyline"

class ComparisonCommandType(Enum):
    CHECK_DRAWN = "Check Drawn"
    CHECK_IN_BATTLE = "Check in Battle"
    MEM_TO_MEM = "Mem to Mem"
    VAL_TO_MEM = "Value to Mem"

class EndCommandType(Enum):
    END = "End"

class FacingCommandType(Enum):
    FACE_OBJECT = "Face Object"
    GET_FACING = "Get Facing"
    SET_FACING = "Set Facing"
    SET_FACING_FROM_MEM = "Set Facing From Mem"

class GotoCommandType(Enum):
    GOTO = "Goto"

class HpMpCommandType(Enum):
    RESTORE_HPMP = "Restore HP/MP"

class InventoryCommandType(Enum):
    EQUIP = "Equip"
    GET_AMOUNT = "Get Item Amount"
    CHECK_GOLD = "Check Gold"
    ADD_GOLD = "Add Gold"
    CHECK_ITEM = "Check Item"
    ITEM = "Item"
    ITEM_FROM_MEM = "Add Item from Mem"

class MemCopyCommandType(Enum):
    MEM_COPY = "Memory Copy"
    MULTI_MODE = "Multi-mode 88"

class Mode7CommandType(Enum):
    DRAW_GEOMETRY = "Draw Geometry"
    MODE7 = "Mode 7"

class ObjectCoordinatesCommandType(Enum):
    GET_OBJ_COORD = "Get Object Coordinates"
    SET_OBJ_COORD = "Set Object Coordinates"
    SET_OBJ_COORD_FROM_MEM = "Set Object Coordinates from Mem"

class ObjectFunctionsCommandType(Enum):
    ACTIVATE = "Activate/Touch"
    CALL_OBJ_FUNC = "Call Object Function"
    SCRIPT_PROCESSING = "Script Processing"

class PaletteCommandType(Enum):
    CHANGE_PALETTE = "Change Palette"

class PauseCommandType(Enum):
    PAUSE = "Pause"

class PartyManagementCommandType(Enum):
    PARTY_MANIP = "Party Manipulation"

class RandomNumberCommandType(Enum):
    RANDOM_NUM = "Random Number"

class SceneManipCommandType(Enum):
    COLOR_ADD = "Color Addition"
    COLOR_MATH = "Color Math"
    COPY_TILES = "Copy Tiles"
    DARKEN = "Darken"
    FADE_OUT = "Fade Out"
    SCRIPT_SPEED = "Script Speed"
    SCROLL_LAYERS = "Scroll Layers"
    SCROLL_LAYERS_2F = "Scroll Layers 2F"
    SCROLL_SCREEN = "Scroll Screen"
    SHAKE_SCREEN = "Shake Screen"
    WAIT_FOR_ADD = "Wait for Color Add End"

class SoundCommandType(Enum):
    SOUND = "Sound"
    WAIT_FOR_SILENCE = "Wait for Silence"

class SpriteCollisionCommandType(Enum):
    SPRITE_COLLISION = "Sprite Collision"

class SpriteDrawingCommandType(Enum):
    DRAW_STATUS = "Drawing Status"
    DRAW_STATUS_FROM_MEM = "Drawing Status from Mem"
    LOAD_SPRITE = "Load Sprite"
    SPRITE_PRIORITY = "Sprite Priority"

class SpriteMovementCommandType(Enum):
    CONTROLLABLE = "Controllable"
    EXPLORE_MODE = "Explore Mode"
    JUMP = "Jump"
    JUMP_7B = "Jump 7B"
    MOVE_PARTY = "Move Party"
    MOVE_SPRITE = "Move Sprite"
    MOVE_SPRITE_FROM_MEM = "Move Sprite from Mem"
    MOVE_TOWARD_COORD = "Move Towards Coordinates"
    MOVE_TOWARD_OBJ = "Move Towards Object"
    OBJECT_FOLLOW = "Object Follow"
    OBJECT_MOVEMENT_PROPERTIES = "Object Movement Properties"
    PARTY_FOLLOW = "Party Follow"
    DESTINATION = "Destination"
    VECTOR_MOVE = "Vector Move"
    VECTOR_MOVE_FROM_MEM = "Vector Move from Mem"
    SET_SPEED = "Set Speed"
    SET_SPEED_FROM_MEM = "Set Speed from Mem"

class TextCommandType(Enum):
    LOAD_ASCII = "Load Ascii"
    SPECIAL_DIALOG = "Special Dialog"
    STRING_INDEX = "String Index"
    TEXTBOX = "Textbox"

class UnknownCommandType(Enum):
    COLOR_CRASH = "Color Crash"
    UNKNOWN = "Unknown"


event_command_groupings = {
    EventCommandType.ANIMATION: {
        AnimationCommandType.ANIMATION: [0xAA, 0xAB, 0xAC, 0xB3, 0xB4, 0xB7],
        AnimationCommandType.ANIMATION_LIMITER: [0x47],
        AnimationCommandType.RESET_ANIMATION: [0xAE],
    },
    EventCommandType.ASSIGNMENT: {
        AssignmentCommandType.GET_PC1: [0x20],
        AssignmentCommandType.GET_STORYLINE: [0x55],
        AssignmentCommandType.MEM_TO_MEM: [0x48, 0x49, 0x4C, 0x4D, 0x51, 0x52, 0x53, 0x54, 0x58, 0x59],
        AssignmentCommandType.RESULT: [0x19, 0x1C],
        AssignmentCommandType.SET_STORYLINE: [0x5A],
        AssignmentCommandType.VALUE_TO_MEM: [0x4A, 0x4B, 0x4F, 0x50, 0x56, 0x75, 0x76, 0x77],
    },
    EventCommandType.BATTLE: {
        BattleCommandType.BATTLE: [0xD8],
    },
    EventCommandType.BIT_MATH: {
        BitMathCommandType.BIT_MATH: [0x63, 0x64, 0x65, 0x66, 0x67, 0x69, 0x6B],
        BitMathCommandType.DOWNSHIFT: [0x6F],
        BitMathCommandType.SET_AT: [0x2A, 0x2B, 0x32],
    },
    EventCommandType.BYTE_MATH: {
        ByteMathCommandType.MEM_TO_MEM: [0x5D, 0x5E, 0x61],
        ByteMathCommandType.VAL_TO_MEM: [0x5B, 0x5F, 0x60, 0x71, 0x72, 0x73],
    },
    EventCommandType.CHANGE_LOCATION: {
        ChangeLocationCommandType.CHANGE_LOCATION: [0xDC, 0xDD, 0xDE, 0xDF, 0xE0, 0xE1],
        ChangeLocationCommandType.CHANGE_LOCATION_FROM_MEM: [0xE2],
    },
    EventCommandType.CHECK_BUTTON: {
        CheckButtonCommandType.CHECK_BUTTON: [0x2D, 0x30, 0x31, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3B, 0x3C, 0x3F, 0x40, 0x41, 0x42, 0x43, 0x44],
    },
    EventCommandType.CHECK_PARTY: {
        CheckPartyCommandType.CHECK_PARTY: [0xCF, 0xD2],
    },
    EventCommandType.CHECK_RESULT: {
        CheckResultCommandType.CHECK_RESULT: [0x1A],
    },
    EventCommandType.CHECK_STORYLINE: {
        CheckStorylineCommandType.CHECK_STORYLINE: [0x18],
    },
    EventCommandType.COMPARISON: {
        ComparisonCommandType.CHECK_DRAWN: [0x27],
        ComparisonCommandType.CHECK_IN_BATTLE: [0x28],
        ComparisonCommandType.MEM_TO_MEM: [0x14, 0x15],
        ComparisonCommandType.VAL_TO_MEM: [0x12, 0x13, 0x16],
    },
    EventCommandType.END: {
        EndCommandType.END: [0x00, 0xB1, 0xB2],
    },
    EventCommandType.FACING: {
        FacingCommandType.FACE_OBJECT: [0xA8, 0xA9],
        FacingCommandType.GET_FACING: [0x23, 0x24],
        FacingCommandType.SET_FACING: [0x0F, 0x17, 0x1B, 0x1D, 0x1E, 0x1F, 0x25, 0x26, 0xA6],
        FacingCommandType.SET_FACING_FROM_MEM: [0xA7],
    },
    EventCommandType.GOTO: {
        GotoCommandType.GOTO: [0x10, 0x11],
    },
    EventCommandType.HP_MP: {
        HpMpCommandType.RESTORE_HPMP: [0xF8, 0xF9, 0xFA]
    },
    EventCommandType.INVENTORY: {
        InventoryCommandType.EQUIP: [0xD5],
        InventoryCommandType.GET_AMOUNT: [0xD7],
        InventoryCommandType.CHECK_GOLD: [0xCC],
        InventoryCommandType.ADD_GOLD: [0xCD, 0xCE],
        InventoryCommandType.CHECK_ITEM: [0xC9],
        InventoryCommandType.ITEM: [0xCA, 0xCB],
        InventoryCommandType.ITEM_FROM_MEM: [0xC7],
    },
    EventCommandType.MEM_COPY: {
        MemCopyCommandType.MEM_COPY: [0x4E],
        MemCopyCommandType.MULTI_MODE: [0x88],
    },
    EventCommandType.MODE7: {
        Mode7CommandType.MODE7: [0xFF],
        Mode7CommandType.DRAW_GEOMETRY: [0xFE],
    },
    EventCommandType.OBJECT_COORDINATES: {
        ObjectCoordinatesCommandType.GET_OBJ_COORD: [0x21, 0x22],
        ObjectCoordinatesCommandType.SET_OBJ_COORD: [0x8B, 0x8D],
        ObjectCoordinatesCommandType.SET_OBJ_COORD_FROM_MEM: [0x8C],
    },
    EventCommandType.OBJECT_FUNCTION: {
        ObjectFunctionsCommandType.ACTIVATE: [0x08, 0x09],
        ObjectFunctionsCommandType.CALL_OBJ_FUNC: [0x02, 0x03, 0x04, 0x05, 0x06, 0x07],
        ObjectFunctionsCommandType.SCRIPT_PROCESSING: [0x0B, 0x0C],
    },
    EventCommandType.PALETTE: {
        PaletteCommandType.CHANGE_PALETTE: [0x33],
    },
    EventCommandType.PAUSE: {
        PauseCommandType.PAUSE: [0xAD, 0xB9, 0xBA, 0xBC, 0xBD],
    },
    EventCommandType.PARTY_MANAGEMENT: {
        PartyManagementCommandType.PARTY_MANIP: [0xD0, 0xD1, 0xD3, 0xD4, 0xD6],
    },
    EventCommandType.RANDOM_NUM: {
        RandomNumberCommandType.RANDOM_NUM: [0x7F],
    },
    EventCommandType.SCENE_MANIP: {
        SceneManipCommandType.COLOR_ADD: [0xF1],
        SceneManipCommandType.COLOR_MATH: [0x2E],
        SceneManipCommandType.COPY_TILES: [0xE4, 0xE5],
        SceneManipCommandType.DARKEN: [0xF0],
        SceneManipCommandType.FADE_OUT: [0xF2],
        SceneManipCommandType.SCRIPT_SPEED: [0x87],
        SceneManipCommandType.SCROLL_LAYERS: [0xE6],
        SceneManipCommandType.SCROLL_LAYERS_2F: [0x2F],
        SceneManipCommandType.SCROLL_SCREEN: [0xE7],
        SceneManipCommandType.SHAKE_SCREEN: [0xF4],
        SceneManipCommandType.WAIT_FOR_ADD: [0xF3],
    },
    EventCommandType.SOUND: {
        SoundCommandType.SOUND: [0xE8, 0xEA, 0xEB, 0xEC],
        SoundCommandType.WAIT_FOR_SILENCE: [0xED, 0xEE],
    },
    EventCommandType.SPRITE_COLLISION: {
        SpriteCollisionCommandType.SPRITE_COLLISION: [0x84],
    },
    EventCommandType.SPRITE_DRAWING: {
        SpriteDrawingCommandType.DRAW_STATUS: [0x0A, 0x7E, 0x90, 0x91],
        SpriteDrawingCommandType.DRAW_STATUS_FROM_MEM: [0x7C, 0x7D],
        SpriteDrawingCommandType.LOAD_SPRITE: [0x57, 0x5C, 0x62, 0x68, 0x6A, 0x6C, 0x6D, 0x80, 0x81, 0x82, 0x83],
        SpriteDrawingCommandType.SPRITE_PRIORITY: [0x8E],
    },
    EventCommandType.SPRITE_MOVEMENT: {
        SpriteMovementCommandType.CONTROLLABLE: [0xAF, 0xB0],
        SpriteMovementCommandType.EXPLORE_MODE: [0xE3],
        SpriteMovementCommandType.JUMP: [0x7A],
        SpriteMovementCommandType.JUMP_7B: [0x7B],
        SpriteMovementCommandType.MOVE_PARTY: [0xD9],
        SpriteMovementCommandType.MOVE_SPRITE: [0x96, 0xA0],
        SpriteMovementCommandType.MOVE_SPRITE_FROM_MEM: [0x97, 0xA1],
        SpriteMovementCommandType.MOVE_TOWARD_COORD: [0x9A],
        SpriteMovementCommandType.MOVE_TOWARD_OBJ: [0x98, 0x99, 0x9E, 0x9F],
        SpriteMovementCommandType.OBJECT_FOLLOW: [0x8F, 0x94, 0x95, 0xB5, 0xB6],
        SpriteMovementCommandType.OBJECT_MOVEMENT_PROPERTIES: [0x0D],
        SpriteMovementCommandType.PARTY_FOLLOW: [0xDA],
        SpriteMovementCommandType.DESTINATION: [0x0E],
        SpriteMovementCommandType.VECTOR_MOVE: [0x92, 0x9C],
        SpriteMovementCommandType.VECTOR_MOVE_FROM_MEM: [0x9D],
        SpriteMovementCommandType.SET_SPEED: [0x89],
        SpriteMovementCommandType.SET_SPEED_FROM_MEM: [0x8A],
    },
    EventCommandType.TEXT: {
        TextCommandType.LOAD_ASCII: [0x29],
        TextCommandType.SPECIAL_DIALOG: [0xC8],
        TextCommandType.STRING_INDEX: [0xB8],
        TextCommandType.TEXTBOX: [0xBB, 0xC0, 0xC1, 0xC2, 0xC3, 0xC4],
    },
    EventCommandType.UNKNOWN: {
        UnknownCommandType.COLOR_CRASH: [0x01],
        UnknownCommandType.UNKNOWN: [0x2C],
    }

}