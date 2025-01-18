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
from editorui.menus.BitMathMenu import BitMathMenu
from editorui.menus.DownshiftMenu import DownshiftMenu
from editorui.menus.SetAtMenu import SetAtMenu
from editorui.menus.MemByteMathMenu import MemByteMathMenu
from editorui.menus.ValByteMathMenu import ValByteMathMenu
from editorui.menus.CheckPartyMenu import CheckPartyMenu
from editorui.menus.CheckResultMenu import CheckResultMenu
from editorui.menus.CheckStorylineMenu import CheckStorylineMenu
from editorui.menus.PauseMenu import PauseMenu
from editorui.menus.GotoMenu import GotoMenu
from editorui.menus.EndMenu import EndMenu
from editorui.menus.HpMpMenu import HPMPMenu
from editorui.menus.ChangeLocationMenu import ChangeLocationMenu
from editorui.menus.CheckDrawnMenu import CheckDrawnMenu
from editorui.menus.CheckInBattleMenu import CheckInBattleMenu
from editorui.menus.ComparisonMenu import ComparisonMenu
from editorui.menus.DrawStatusMenu import DrawStatusMenu
from editorui.menus.DrawStatusFromMemMenu import DrawStatusFromMemMenu
from editorui.menus.LoadSpriteMenu import LoadSpriteMenu
from editorui.menus.SpritePriorityMenu import SpritePriorityMenu
from editorui.menus.WaitForAddMenu import WaitForAddMenu
from editorui.menus.ShakeScreenMenu import ShakeScreenMenu
from editorui.menus.ScrollScreenMenu import ScrollScreenMenu
from editorui.menus.FadeOutMenu import FadeOutMenu
from editorui.menus.DarkenMenu import DarkenMenu
from editorui.menus.ColorAddMenu import ColorAddMenu
from editorui.menus.MemCopyMenu import MemCopyMenu
from editorui.menus.MultiModeMenu import MultiModeMenu


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
    EventCommandType.BIT_MATH: {
        EventCommandSubtype.BIT_MATH: BitMathMenu(),
        EventCommandSubtype.DOWNSHIFT: DownshiftMenu(),
        EventCommandSubtype.SET_AT: SetAtMenu(),
    },
    EventCommandType.BYTE_MATH: {
        EventCommandSubtype.MEM_TO_MEM_BYTE: MemByteMathMenu(), # not sure about this
        EventCommandSubtype.VAL_TO_MEM_BYTE: ValByteMathMenu(),

    },
    EventCommandType.CHANGE_LOCATION: {
        EventCommandSubtype.CHANGE_LOCATION: ChangeLocationMenu()
    },
    EventCommandType.CHECK_BUTTON: {
        EventCommandSubtype.CHECK_BUTTON: CheckButtonMenu()
    },
    EventCommandType.CHECK_PARTY: {
        EventCommandSubtype.CHECK_PARTY: CheckPartyMenu()
    },
    EventCommandType.CHECK_RESULT: {
        EventCommandSubtype.CHECK_RESULT: CheckResultMenu()
    },
    EventCommandType.CHECK_STORYLINE: {
        EventCommandSubtype.CHECK_STORYLINE: CheckStorylineMenu()
    },
    EventCommandType.COMPARISON: {
        EventCommandSubtype.CHECK_DRAWN: CheckDrawnMenu(),
        EventCommandSubtype.CHECK_IN_BATTLE: CheckInBattleMenu(),
        EventCommandSubtype.MEM_TO_MEM_COMP: ComparisonMenu(),
        EventCommandSubtype.VAL_TO_MEM_COMP: ComparisonMenu(),
    },
    EventCommandType.END: {
        EventCommandSubtype.END: EndMenu()
    },
    EventCommandType.FACING: {},
    EventCommandType.GOTO: {
        EventCommandSubtype.GOTO: GotoMenu()
    },
    EventCommandType.HP_MP: {
        EventCommandSubtype.RESTORE_HPMP: HPMPMenu()
    },
    EventCommandType.INVENTORY: {
        EventCommandSubtype.EQUIP: EquipItemMenu(),
        EventCommandSubtype.GET_AMOUNT: GetItemQuantityMenu(),
        EventCommandSubtype.CHECK_GOLD: CheckGoldMenu(),
        EventCommandSubtype.ADD_GOLD: AddGoldMenu(),
        EventCommandSubtype.CHECK_ITEM: ItemMenu(),
        EventCommandSubtype.ITEM: ItemMenu(),
        EventCommandSubtype.ITEM_FROM_MEM: ItemFromMemMenu()
    },
    EventCommandType.MEM_COPY: {
        EventCommandSubtype.MEM_COPY: MemCopyMenu(),
        EventCommandSubtype.MULTI_MODE: MultiModeMenu(),
    },
    EventCommandType.MODE7: {},
    EventCommandType.OBJECT_COORDINATES: {},
    EventCommandType.OBJECT_FUNCTION: {},
    EventCommandType.PALETTE: {
        EventCommandSubtype.CHANGE_PALETTE: ChangePaletteMenu()
    },
    EventCommandType.PAUSE: {
        EventCommandSubtype.PAUSE: PauseMenu(),
    },
    EventCommandType.PARTY_MANAGEMENT: {},
    EventCommandType.RANDOM_NUM: {
        EventCommandSubtype.RANDOM_NUM: RandomNumberMenu()
    },
    EventCommandType.SCENE_MANIP: {
        EventCommandSubtype.SCRIPT_SPEED: ScriptSpeedMenu(),
        EventCommandSubtype.COLOR_ADD: ColorAddMenu(),
        EventCommandSubtype.DARKEN: DarkenMenu(),
        EventCommandSubtype.FADE_OUT: FadeOutMenu(),
        EventCommandSubtype.SCROLL_SCREEN: ScrollScreenMenu(),
        EventCommandSubtype.SHAKE_SCREEN: ShakeScreenMenu(),
        EventCommandSubtype.WAIT_FOR_ADD: WaitForAddMenu(),
    },
    EventCommandType.SOUND: {},
    EventCommandType.SPRITE_COLLISION: {
        EventCommandSubtype.SPRITE_COLLISION: SpriteCollisionMenu()
    },
    EventCommandType.SPRITE_DRAWING: {
        EventCommandSubtype.SPRITE_PRIORITY: SpritePriorityMenu(),
        EventCommandSubtype.LOAD_SPRITE: LoadSpriteMenu(),
        EventCommandSubtype.DRAW_STATUS: DrawStatusMenu(),
        EventCommandSubtype.DRAW_STATUS_FROM_MEM: DrawStatusFromMemMenu(),
    },
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