from editorui.commandgroups import EventCommandType, EventCommandSubtype
from editorui.menus.EquipItemMenu import EquipItemMenu
from editorui.menus.UnassignedMenu import UnassignedMenu
from editorui.menus.GetItemQuantityMenu import GetItemQuantityMenu
from editorui.menus.CheckGoldMenu import CheckGoldMenu
from editorui.menus.AddGoldMenu import AddGoldMenu
from editorui.menus.ItemMenu import ItemMenu
from editorui.menus.ItemFromMemMenu import ItemFromMemMenu
from editorui.menus.StringIndexMenu import StringIndexMenu
from editorui.menus.SpecialDialogMenu import SpecialDialogMenu
from editorui.menus.TextboxMenu import TextboxMenu
from editorui.menus.AnimationLimiterMenu import AnimationLimiterMenu
from editorui.menus.AnimationMenu import AnimationMenu
from editorui.menus.BattleMenu import BattleMenu
from editorui.menus.ChangePaletteMenu import ChangePaletteMenu
from editorui.menus.CheckButtonMenu import CheckButtonMenu
from editorui.menus.ControllableMenu import ControllableMenu
from editorui.menus.DestinationPropertiesMenu import DestinationPropertiesMenu
from editorui.menus.ExploreModeMenu import ExploreModeMenu
from editorui.menus.FollowTargetMenu import FollowTargetMenu
from editorui.menus.GetPC1Menu import GetPC1Menu
from editorui.menus.GetStoryCtrMenu import GetStoryCtrMenu
from editorui.menus.LoadASCIIMenu import LoadASCIIMenu
from editorui.menus.MemToMemAssignMenu import MemToMemAssignMenu
from editorui.menus.MovePartyMenu import MovePartyMenu
from editorui.menus.MoveSpriteFromMemMenu import MoveSpriteFromMemMenu
from editorui.menus.MoveSpriteMenu import MoveSpriteMenu
from editorui.menus.MoveTowardCoordMenu import MoveTowardCoordMenu
from editorui.menus.MoveTowardTargetMenu import MoveTowardTargetMenu
from editorui.menus.ObjectMovementPropertiesMenu import ObjectMovementPropertiesMenu
from editorui.menus.PartyFollowMenu import PartyFollowMenu
from editorui.menus.RandomNumberMenu import RandomNumberMenu
from editorui.menus.ResetAnimationMenu import ResetAnimationMenu
from editorui.menus.ResultMenu import ResultMenu
from editorui.menus.ScriptSpeedMenu import ScriptSpeedMenu
from editorui.menus.SetSpeedMenu import SetSpeedMenu
from editorui.menus.SetStorylineMenu import SetStorylineMenu
from editorui.menus.SpriteCollisionMenu import SpriteCollisionMenu
from editorui.menus.ValToMemAssignMenu import ValToMemAssignMenu
from editorui.menus.VectorMoveMenu import VectorMoveMenu

menu_mapping = {
    EventCommandType.UNASSIGNED: {
        EventCommandSubtype.UNASSIGNED: UnassignedMenu()
    },
    EventCommandType.ANIMATION: {
        EventCommandSubtype.ANIMATION: AnimationMenu(),
        EventCommandSubtype.ANIMATION_LIMITER: AnimationLimiterMenu(),
        EventCommandSubtype.RESET_ANIMATION: ResetAnimationMenu()
    },
    EventCommandType.ASSIGNMENT: {
        EventCommandSubtype.GET_PC1: GetPC1Menu(),
        EventCommandSubtype.GET_STORYLINE: GetStoryCtrMenu(),
        EventCommandSubtype.MEM_TO_MEM_ASSIGN: MemToMemAssignMenu(),
        EventCommandSubtype.RESULT: ResultMenu(),
        EventCommandSubtype.SET_STORYLINE: SetStorylineMenu(),
        EventCommandSubtype.VAL_TO_MEM_ASSIGN: ValToMemAssignMenu(),
    },  
    EventCommandType.BATTLE: {
        EventCommandSubtype.BATTLE: BattleMenu()
    },
    EventCommandType.BIT_MATH: {},
    EventCommandType.BYTE_MATH: {},
    EventCommandType.CHANGE_LOCATION: {},
    EventCommandType.CHECK_BUTTON: {
        EventCommandSubtype.CHECK_BUTTON: CheckButtonMenu()
    },
    EventCommandType.CHECK_PARTY: {},
    EventCommandType.CHECK_RESULT: {},
    EventCommandType.CHECK_STORYLINE: {},
    EventCommandType.COMPARISON: {},
    EventCommandType.END: {},
    EventCommandType.FACING: {},
    EventCommandType.GOTO: {},
    EventCommandType.HP_MP: {},
    EventCommandType.INVENTORY: {
        EventCommandSubtype.EQUIP: EquipItemMenu(),
        EventCommandSubtype.GET_AMOUNT: GetItemQuantityMenu(),
        EventCommandSubtype.CHECK_GOLD: CheckGoldMenu(),
        EventCommandSubtype.ADD_GOLD: AddGoldMenu(),
        EventCommandSubtype.CHECK_ITEM: ItemMenu(),
        EventCommandSubtype.ITEM: ItemMenu(),
        EventCommandSubtype.ITEM_FROM_MEM: ItemFromMemMenu()
    },
    EventCommandType.MEM_COPY: {},
    EventCommandType.MODE7: {},
    EventCommandType.OBJECT_COORDINATES: {},
    EventCommandType.OBJECT_FUNCTION: {},
    EventCommandType.PALETTE: {
        EventCommandSubtype.CHANGE_PALETTE: ChangePaletteMenu()
    },
    EventCommandType.PAUSE: {},
    EventCommandType.PARTY_MANAGEMENT: {},
    EventCommandType.RANDOM_NUM: {
        EventCommandSubtype.RANDOM_NUM: RandomNumberMenu()
    },
    EventCommandType.SCENE_MANIP: {
        EventCommandSubtype.SCRIPT_SPEED: ScriptSpeedMenu()
    },
    EventCommandType.SOUND: {},
    EventCommandType.SPRITE_COLLISION: {
        EventCommandSubtype.SPRITE_COLLISION: SpriteCollisionMenu()
    },
    EventCommandType.SPRITE_DRAWING: {},
    EventCommandType.SPRITE_MOVEMENT: {
        EventCommandSubtype.CONTROLLABLE: ControllableMenu(),
        EventCommandSubtype.EXPLORE_MODE: ExploreModeMenu(),
        # Jump
        # Jump 7B
        EventCommandSubtype.MOVE_PARTY: MovePartyMenu(),
        EventCommandSubtype.MOVE_SPRITE: MoveSpriteMenu(),
        EventCommandSubtype.MOVE_SPRITE_FROM_MEM: MoveSpriteFromMemMenu(),
        EventCommandSubtype.MOVE_TOWARD_COORD: MoveTowardCoordMenu(),
        EventCommandSubtype.MOVE_TOWARD_OBJ: MoveTowardTargetMenu(),
        EventCommandSubtype.OBJECT_FOLLOW: FollowTargetMenu(),
        EventCommandSubtype.OBJECT_MOVEMENT_PROPERTIES: ObjectMovementPropertiesMenu(),
        EventCommandSubtype.PARTY_FOLLOW: PartyFollowMenu(),
        EventCommandSubtype.DESTINATION: DestinationPropertiesMenu(),
        EventCommandSubtype.VECTOR_MOVE: VectorMoveMenu(),
        #EventCommandSubtype.VECTOR_MOVE_FROM_MEM: 
        EventCommandSubtype.SET_SPEED: SetSpeedMenu(),
        # EventCommandSubtype.SET_SPEED_FROM_MEM: 
    },
    EventCommandType.TEXT: {
        EventCommandSubtype.LOAD_ASCII: LoadASCIIMenu(),
        EventCommandSubtype.SPECIAL_DIALOG: SpecialDialogMenu(),
        EventCommandSubtype.STRING_INDEX: StringIndexMenu(),
        EventCommandSubtype.TEXTBOX: TextboxMenu()
    },
}