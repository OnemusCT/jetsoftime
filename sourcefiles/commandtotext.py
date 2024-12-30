from eventcommand import Operation, EventCommand
from location_data import locations

def command_to_text(command: EventCommand, bytes: int) -> str:
    command_str = command.to_human_readable_str()
    if command.command in _command_to_text:
        if isinstance(_command_to_text[command.command], str):
            command_str = _command_to_text[command.command].format(*command.args)
        elif command.command == 0x10 or command.command == 0x11:
            command_str = _command_to_text[command.command](command.args, bytes)
        else:
            command_str = _command_to_text[command.command](command.args)
    return command_str

operations = {
    Operation.EQUALS: "==",
    Operation.GREATER_THAN: ">",
    Operation.GREATER_OR_EQUAL: ">=",
    Operation.LESS_THAN: "<",
    Operation.LESS_OR_EQUAL: "<=",
    Operation.NOT_EQUALS: "!=",
    Operation.BITWISE_AND_NONZERO: "&",
    Operation.BITWISE_OR_NONZERO: "|",
}

def val_to_obj(obj: int) -> int:
    return int(obj/2)

def address_offset(offset: int) -> int:
    return (offset*2) + 0x7f0200

def local_address_offset(offset: int) -> int:
    return offset + 0x7f0000


def operation_to_str(operation: Operation) -> str:
    return operations.get(operation % 0x10)

def disable_processing(args) -> str:
    return "Disable Processing(Obj{:02X})".format(val_to_obj(args[0]))

def enable_processing(args) -> str:
    return "Enable Processing(Obj{:02X})".format(val_to_obj(args[0]))

def hide_obj(args) -> str:
    return "Hide Object(Obj{:02X})".format(val_to_obj(args[0]))

def if_val(args) -> str:
    return "If(0x{:02X} {} {:02X})".format(address_offset(args[0]), operation_to_str(args[2]), args[1])

def if_local_val(args) -> str:
    return "If(0x{:02X} {} {:02X})".format(local_address_offset(args[0]), operation_to_str(args[2]), args[1])

def if_address(args) -> str:
    return "If(0x{:02X} {} {:02X})".format(address_offset(args[0]), operation_to_str(args[2]), args[1])

def if_local_address(args) -> str:
    return "If(0x{:02X} {} 0x{:02X})".format(local_address_offset(args[0]), operation_to_str(args[2]), address_offset(args[1]))

def if_visible(args) -> str:
    return "If(Obj{} visible)".format(val_to_obj(args[0]))

def if_battle_range(args) ->str:
    return "If(Obj{} in battle range)".format(val_to_obj(args[0]))

def get_result_7f0200(args) -> str:
    return "Get Result(0x{:02X})".format(address_offset(args[0]))

def get_result_7f0000(args) ->str:
    return "Get Result(0x{:02X})".format(0x7f0000 + args[0])

def load_pc(args) -> str:
    return "Load PC1 into 0x{:02X}".format(address_offset(args[0]))

def load_obj_coords(args) -> str:
    return "Load Obj{} Coords into 0x{:02X},0x{:02X}".format(val_to_obj(args[0]), (args[1]*2)+0x7f0200, (args[2]*2)+0x7f0200)

def load_pc_coords(args) -> str:
    return "Load PC{} Coords into 0x{:02X},0x{:02X}".format(val_to_obj(args[0]), (args[1]*2)+0x7f0200, (args[2]*2)+0x7f0200)

def load_obj_facing(args) -> str:
    return "Load Obj{} Facing into 0x{:02X}".format(val_to_obj(args[0]), (args[1]*2)+0x7f0200)

def load_pc_facing(args) -> str:
    return "Load PC{} Facing into 0x{:02X}".format(val_to_obj(args[0]), (args[1]*2)+0x7f0200)

def assign_local(args) -> str:
    return "Set 0x{:02X} = 0x{:02X}".format(args[1], 0x7f0200 + (args[0]*2))

def assign_48(args) -> str:
    return "Set 0x{:02X} = 0x{:02X}".format(0x7f0200 + (args[1]*2), args[0])


def assign_from_local(args) -> str:
    return "Set 0x{:02X} = 0x{:02X}".format(0x7f0200 + (args[0]*2), args[0])

def assign_address(args) -> str:
    return "Set 0x{:02X} = {:02X}".format(args[0], args[1])

def npc_movement_properties(args) -> str:
    return "NPC Movement Properties(Through Walls: {}, Through PCs: {})".format(bool(args[0] and 1), bool(args[0] and 2))

def assign_val_to_mem(args) -> str:
    return "Set 0x{:02X} = {:02X}".format(args[1]*2+0x7f0200, args[0])

def assign_mem_to_mem(args) -> str:
    return "Set 0x{:02X} = 0x{:02X}".format(args[1]*2+0x7f0200, args[0]*2+0x7f0200)

def assign_local_mem_to_mem(args) -> str:
    return "Set 0x{:02X} = 0x{:02X}".format(args[1]*2+0x7f0200, args[0]+0x7f0000)

def assign_mem_to_local_mem(args) -> str:
    return "Set 0x{:02X} = 0x{:02X}".format(args[1]+0x7f0000, args[0]*2+0x7f0200)

def assign_val_to_mem_local(args) -> str:
    return "Set 0x{:02X} = {:02X}".format(args[1]+0x7f0000, args[0])

def get_storyline(args) -> str:
    return "Set 0x{:02X} = Storyline".format(args[0]*2+0x7f0200)

def add_val_to_mem_local(args) -> str:
    return "0x{:02X} += {:02X}".format(args[1]*2+0x7f0200, args[0])

def add_mem_to_mem(args) -> str:
    return "0x{:02X} += 0x{:02X}".format(args[1]*2+0x7f0200, args[0]*2+0x7f0200)

def goto_forward(args, curr_bytes):
    return "Goto(0x{:02X})".format(args[-1] + curr_bytes + 1)

def goto_backward(args, curr_bytes):
    return "Goto(0x{:02X})".format(curr_bytes - args[-1] + 1)

def change_location(args) -> str:
    for (id, name) in locations:
        if args[0] == id:
            return "Change Location({}, {},{})".format(name, args[1], args[2])
    return "Change Location({:02X}, {},{})".format(args[0], args[1], args[2])

_command_to_text = {
    0x00: "Return",
    0x01: "Color Crash",
    0x02: "Call Event({:02X} {:02X})",
    0x03: "Call Event({:02X} {:02X})",
    0x04: "Call Event({:02X} {:02X})",
    0x05: "Call Event({:02X} {:02X})",
    0x06: "Call PC Event({} {:02X})",
    0x07: "Call PC Event({} {:02X})",
    0x08: "Deactivate Object",
    0x09: "Activate Object",
    0x0A: hide_obj,
    0x0B: disable_processing,
    0x0C: enable_processing,
    0x0D: npc_movement_properties,
    0x0E: "Unknown NPC Positioning({:02X})",
    0x0F: "Set NPC Facing Up",
    0x10: goto_forward,
    0x11: goto_backward,
    0x12: if_val,
    0x13: if_val,
    0x14: if_address,
    0x15: if_address,
    0x16: if_local_val,
    0x17: "Set NPC Facing Down",
    0x18: "If(Storyline < {:02X})",
    0x19: get_result_7f0200,
    0x1A: "If(!{:02X})",
    0x1B: "Set NPC Facing Left",
    0x1C: get_result_7f0000,
    0x1D: "Set NPC Facing Right",
    0x1E: "Set NPC ({}) Facing Up",
    0x1F: "Set NPC ({}) Facing Down",
    0x20: load_pc,
    0x21: load_obj_coords,
    0x22: load_pc_coords,
    0x23: load_obj_facing,
    0x24: load_pc_facing,
    0x25: "Set NPC({}) Facing Left",
    0x26: "Set NPC({}) Facing Right",
    0x27: if_visible,
    0x28: if_battle_range,
    0x29: "Load Ascii Text({:02X})",
    0x2A: "Unknown 0x2A",
    0x2B: "Unknown 0x2B",
    0x2C: "Unknown 0x2C",
    0x2D: "If(no buttons pressed)",
    0x2E: "Color Math (mode: {})",
    0x2F: "Unknown 0x2F",
    0x30: "If(dashing)",
    0x31: "If(confirm)",
    0x32: "Unknown 0x32",
    0x33: "Change Palette to {:02X}",
    0x34: "If(A pressed)",
    0x35: "If(B pressed)",
    0x36: "If(X pressed)",
    0x37: "If(Y pressed)",
    0x38: "If(L pressed)",
    0x39: "If(R pressed)",
    0x3A: "Color crash",
    0x3B: "If(dashing since last check)",
    0x3C: "If(confirm since last check)",
    0x3D: "Color crash",
    0x3E: "Color crash",
    0x3F: "If(A pressed since last check)",
    0x40: "If(B pressed since last check)",
    0x41: "If(X pressed since last check)",
    0x42: "If(Y pressed since last check)",
    0x43: "If(L pressed since last check)",
    0x44: "If(R pressed since last check)",
    0x45: "Color crash",
    0x46: "Color crash",
    0x47: "Limit Animations({:02X})",
    0x48: assign_48,
    0x49: assign_local,
    0x4A: assign_address,
    0x4B: assign_address,
    0x4C: assign_from_local,
    0x4D: assign_from_local,
    0x4E: "Mem Copy({:02X} {:02X} bytes to copy {:02X})",
    0x4F: assign_val_to_mem,
    0x50: assign_val_to_mem,
    0x51: assign_mem_to_mem,
    0x52: assign_mem_to_mem,
    0x53: assign_local_mem_to_mem,
    0x54: assign_local_mem_to_mem,
    0x55: get_storyline,
    0x56: assign_val_to_mem_local,
    0x57: "Load Crono",
    0x58: assign_mem_to_local_mem,
    0x59: assign_mem_to_local_mem,
    0x5A: "Set Storyline = {:02X}",
    0x5B: add_val_to_mem_local,
    0x5C: "Load Marle",
    0x5D: add_mem_to_mem,
    0x5E: add_mem_to_mem,
    #0x5F:
    0xE0: change_location,
    0xE1: change_location,
}