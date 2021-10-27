# This module makes classes for storing a configuration of the randomizer.
# Each module of the randomizer will get passed the GameConfig object and the
# flags and update the GameConfig.  Then, the randomizer will write the
# GameConfig out to the rom.
from __future__ import annotations
from io import BufferedWriter

from byteops import to_little_endian, get_value_from_bytes, to_file_ptr

from bossdata import get_boss_data_dict
from ctenums import ItemID, LocID, TreasureID as TID, CharID, ShopID, \
    RecruitID, BossID
import techdb
# from ctevent import ScriptManager as SM, Event
from ctrom import CTRom
from freespace import FSWriteType  # Only for the test main() code
import enemystats
import statcompute


class PlayerChar:

    def __init__(self, rom: bytearray, pc_id: CharID,
                 stat_start: int = 0x0C0000,
                 hp_growth_start: int = 0x0C25A8,
                 mp_growth_start: int = 0x0C25C2,
                 stat_growth_start: int = 0x0C25FA,
                 xp_thresh_start: int = 0x0C2632,
                 tp_thresh_start: int = 0x0C26FA):

        self.stats = statcompute.PCStats.stats_from_rom(
            rom, pc_id, stat_start, hp_growth_start, mp_growth_start,
            stat_growth_start, xp_thresh_start, tp_thresh_start
        )

        self.pc_id = pc_id

        # These are for bookkeeping.  They're stored here but the write
        # is guaranteed elsewhere
        self.tech_permutation = [x for x in range(8)]
        self.assigned_char = pc_id

    # Being explicit here that we only write out the stats.
    def write_stats_to_ctrom(self, ctrom: CTRom,
                             stat_start: int = 0x0C0000,
                             hp_growth_start: int = 0x0C25A8,
                             mp_growth_start: int = 0x0C25C2,
                             stat_growth_start: int = 0x0C25FA,
                             tp_thresh_start: int = 0x0C26FA):
        # TODO: Try to read these x_start pointers from the rom
        self.stats.write_to_rom(ctrom.rom_data.getbuffer(),
                                self.pc_id,
                                stat_start,
                                hp_growth_start,
                                mp_growth_start,
                                stat_growth_start,
                                tp_thresh_start)


# Class that handles data related to PCs.
# For now it will handle writing stats to the rom.  The other data is mainly
# for tracking purposes and will be written out by other files.
# The end goal is for everything PC-related to be managed here.
class CharManager:

    # TODO: Read all of these pointers from the rom.  On the other hand,
    # they are unlikely to change (except when charrando moves them to
    # another block at the last minute).
    def __init__(self, rom: bytearray,
                 stat_start: int = 0x0C0000,
                 hp_growth_start: int = 0x0C258A,
                 mp_growth_start: int = 0x0C25C2,
                 stat_growth_start: int = 0xC25FA,
                 xp_thresh_start: int = 0x0C2632,
                 tp_thresh_start: int = 0x0C26FA):
        self.stat_start = stat_start
        self.hp_growth_start = hp_growth_start
        self.mp_growth_start = mp_growth_start
        self.stat_growth_start = stat_growth_start
        self.xp_thresh_start = xp_thresh_start
        self.tp_thresh_start = tp_thresh_start

        self.pcs = [
            PlayerChar(
                rom, CharID(i), self.stat_start, self.hp_growth_start,
                self.mp_growth_start, self.stat_growth_start,
                self.xp_thresh_start, self.tp_thresh_start
            ) for i in range(7)]

    def write_stats_to_ctrom(self, ctrom: CTRom):
        for pc in self.pcs:
            pc.write_stats_to_ctrom(ctrom)


# Class that handles storing and manipulating item prices
class PriceManager:

    def __init__(self, rom: bytearray):
        self.price_dict = dict()

        for item in list(ItemID):
            price_addr = self.__get_price_addr(item)
            price = get_value_from_bytes(rom[price_addr:price_addr+2])
            self.price_dict[item] = price
            # Note:  In the future we could be adding a per-shop price
            #        multiplier to go along with the item list.

    def get_price(self, item: ItemID):
        return self.price_dict[item]

    def set_price(self, item: ItemID, price: int):
        if price > 0xFFFF:
            print('Error: price exceeds 0xFFFF.  Not Changing.')
            input()
        else:
            self.price_dict[item] = price

    def write_to_ctrom(self, ctrom: CTRom):
        rom = ctrom.rom_data

        for item, price in self.price_dict.items():
            addr = self.__get_price_addr(item)
            rom.seek(addr)
            rom.write(to_little_endian(price, 2))

    # Following pointers from original shopwriter
    @classmethod
    def __get_price_addr(cls, item: ItemID) -> int:
        # We're assuming this is all vanilla.  Otherwise we need to pass
        # a rom in here too.

        item_index = int(item)

        # Different types of items have their price data in different places
        if item_index < 0x94:
            # Gear is in 00 (empty) to 0x93 (Mermaid Cap)
            # 6 byte record, price is 2 bytes, offset 1
            return 0x0C06A4 + 6*item_index + 1
        elif item_index < 0xBC:
            # Accessories in 0x94 (empty) to 0xBB (Prismspecs)
            # 4 byte record, price is 2 bytes, offset 1
            return 0x0C0A1C + 4*(item_index-0x94) + 1
        else:
            # Consumables + Keys in 0xBC (empty) to 0xE7 (2xFeather)
            # 3 byte record, price is 2 bytes, offset 1
            return 0x0C0ABC + 3*(item_index-0xBC) + 1

    def __str__(self):
        ret = ''
        for item, price in self.price_dict.items():
            ret += f"{item}: {price}\n"

        return ret


class ShopManager:

    shop_ptr = 0x02DAFD
    shop_data_bank_ptr = 0x02DB09

    def __init__(self, rom: bytearray):

        shop_data_bank, shop_ptr_start = ShopManager.__get_shop_pointers(rom)

        # print(f"Shop data bank = {self.shop_data_bank:06X}")
        # print(f"Shop ptr start = {self.shop_ptr_start:06X}")

        # We're using some properties of ShopID here.
        #  1) ShopID starts from 0x00, and
        #  2) ShopID contains all values from 0x00 to N-1 where N is
        #     the number of shops.

        self.shop_dict = dict()

        # The sort shouldn't be necessary, but be explicit.
        for shop in sorted(list(ShopID)):
            index = int(shop)
            ptr_start = shop_ptr_start + 2*index
            shop_ptr_local = get_value_from_bytes(rom[ptr_start:ptr_start+2])
            shop_ptr = shop_ptr_local + shop_data_bank
            shop_ptr = shop_ptr

            pos = shop_ptr
            self.shop_dict[shop] = []

            # Items in the shop are a 0-terminated list
            while rom[pos] != 0:
                # print(ItemID(rom[pos]))
                self.shop_dict[shop].append(ItemID(rom[pos]))
                pos += 1

    # Returns start of shop pointers, start of bank of shop data
    @classmethod
    def __get_shop_pointers(cls, rom: bytearray):
        shop_data_bank = to_file_ptr(rom[cls.shop_data_bank_ptr] << 16)
        shop_ptr_start = \
            to_file_ptr(
                get_value_from_bytes(rom[cls.shop_ptr:cls.shop_ptr+3])
            )
        return shop_data_bank, shop_ptr_start

    def write_to_ctrom(self, ctrom: CTRom):
        # The space used/freed by TF isn't available to me.  I just have to
        # assume that the space currently allotted is enough.

        shop_data_bank, shop_ptr_start = \
            ShopManager.__get_shop_pointers(ctrom.rom_data.getbuffer())

        rom = ctrom.rom_data

        ptr_loc = shop_ptr_start
        rom.seek(ptr_loc)
        data_loc = get_value_from_bytes(rom.read(2)) + shop_data_bank

        max_index = max(self.shop_dict.keys())

        for shop_id in range(max_index+1):
            shop = ShopID(shop_id)

            rom.seek(ptr_loc)
            ptr = data_loc % 0x010000
            ptr_loc += rom.write(to_little_endian(ptr, 2))

            if shop in self.shop_dict.keys():
                items = bytearray(self.shop_dict[shop]) + b'\x00'
            else:
                items = bytearray([ItemID.MOP]) + b'\x00'

            rom.seek(data_loc)
            data_loc += rom.write(items)

    def set_shop_items(self, shop: ShopID, items: list[ItemID]):
        self.shop_dict[shop] = items[:]

    def print_with_prices(self, price_manager: PriceManager):
        print(self.__str__(price_manager))

    def __str__(self, price_manager: PriceManager = None):
        ret = ''
        for shop in sorted(self.shop_dict.keys()):
            if shop in [ShopID.EMPTY_12, ShopID.EMPTY_14,
                        ShopID.LAST_VILLAGE_UPDATED]:
                continue
            
            ret += str(shop)
            ret += ':\n'
            for item in self.shop_dict[shop]:
                ret += ('    ' + str(item))

                if price_manager is not None:
                    price = price_manager.get_price(item)
                    ret += f": {price}"

                ret += '\n'

        return ret


# All CharRecruits are script-based
# Parameters are self explanatory except for load_obj_id and recruit_obj_id
# Sometimes the character sprite is located in a different object than the code
# which actually adds the character to the team.  So the sprite's object is
# load_obj_id and the code that adds the character is recruit_obj_id
class CharRecruit:

    # Indexed by CharID, so load_cmds[CharID.Crono] is Crono's load cmd
    load_cmds = [0x57, 0x5C, 0x62, 0x6A, 0x68, 0x6C, 0x6D]

    def __init__(self, held_char: CharID,
                 loc_id: LocID,
                 load_obj_id: int,
                 recruit_obj_id: int):
        self.held_char = held_char
        self.loc_id = loc_id
        self.load_obj_id = load_obj_id
        self.recruit_obj_id = recruit_obj_id

    # This might be poor naming, but the writing goes to the script manager
    # of the ctrom.  A separate call has to commit those changes to the rom.
    def write_to_ctrom(self, ctrom: CTRom):
        script_manager = ctrom.script_manager
        script = script_manager.get_script(self.loc_id)

        start = script.get_object_start(self.load_obj_id)
        end = script.get_object_end(self.load_obj_id)

        # First find the load command that's already in the script
        # There should be a LoadPC (not in party) command before any other
        # pc-related commands.  This has command id = 0x81.

        pos, cmd = script.find_command([0x81], start, end)

        if pos is None:
            print('Error finding initial load')
            print(self.loc_id, self.object_id)
            exit()

        script.data[pos+1] = int(self.held_char)

        orig_char = CharID(cmd.args[0])
        orig_load_cmd = CharRecruit.load_cmds[orig_char]
        target_load_cmd = CharRecruit.load_cmds[self.held_char]

        # Now handle the recruitment
        pos = script.get_object_start(self.recruit_obj_id)
        end = script.get_object_end(self.recruit_obj_id)

        while pos < end:
            # character manip commands:
            # 0x81 - Load out of party charater: 1st arg pc_id
            # 0xD2 - If PC is active: 1st arg pc_id
            # 0xCF - If PC is recruited: 1st arg pc_id
            # 0xC8 - Special Dialog (name): 1st arg pc_id | 0xC0
            # 0xD0 - Add PC to Reserve: 1st arg pc_id
            # the load command is pc-specific, 0 arg

            (pos, cmd) = \
                script.find_command(
                    [0x81, 0xD2, 0xCF, 0xC8, 0xD0, 0xD3] + [orig_load_cmd],
                    pos, end
                )

            if pos is None:
                break

            # cmds that just need the pc id written
            if cmd.command in [0x81, 0xD2, 0xCF, 0xD0, 0xD3]:
                script.data[pos+1] = int(self.held_char)
            elif cmd.command == 0xC8:
                script.data[pos+1] = int(self.held_char | 0xC0)
            elif cmd.command == orig_load_cmd:
                script.data[pos] == target_load_cmd
            else:
                print(f"Error, uncaught command ({cmd.command:02X})")
                exit()

            pos += len(cmd)


class StarterChar:

    def __init__(self,
                 loc_id: LocID = LocID.LOAD_SCREEN,
                 object_id: int = 0,
                 function_id: int = 0,
                 held_char: CharID = CharID.CRONO,
                 starter_num=0):
        self.loc_id = loc_id
        self.object_id = object_id
        self.function_id = function_id
        self.held_char = held_char
        self.starter_num = starter_num

    def write_to_ctrom(self, ctrom: CTRom):
        script_manager = ctrom.script_manager
        script = script_manager.get_script(self.loc_id)

        start = script.get_function_start(self.object_id, self.function_id)
        end = script.get_function_end(self.object_id, self.function_id)

        num_name_char = 0
        num_add_party = 0

        pos = start
        while (num_name_char != self.starter_num+1 or
               num_add_party != self.starter_num+1):

            # 0xD3 - Add to active party: 1st arg pc_id
            # 0xC8 - Special Dialog (name): 1st arg pc_id | 0xC0
            pos, cmd = script.find_command([], pos, end)

            if pos is None:
                print("Error: Hit end of function before finding character.")
                exit()

            if cmd.command == 0xD3:
                if num_add_party == self.starter_num:
                    script.data[pos+1] = int(self.held_char)

                num_add_party += 1
            elif cmd.command == 0xC8:
                if num_name_char == self.starter_num:
                    script.data[pos+1] = int(self.held_char) | 0xC0

                num_name_char += 1

            pos += len(cmd)


class Treasure:

    def __init__(self, held_item: ItemID = ItemID.MOP):
        self.held_item = held_item

    def write_to_ctrom(self, ctrom: CTRom):
        raise NotImplementedError


# Treasures that are obtained through a regular chest
class ChestTreasure(Treasure):

    # pointer to the start of the treasure data
    # Treasure Data (from db)
    #   bytes 0,1: x and y coords (if blank does something weird)
    #   bytes 2,3: 0x80 = Gold Flag, 0x40 = Empty Flag 0x3FFF = contents
    #              If gold flag is set, 0x7FFF = gold amount / 2
    # Since it's little endian the bits are flag bits are the leading bits
    # of byte 3.

    treasure_ptr = 0x35F402

    def __init__(self, chest_index, held_item=ItemID.MOP):
        super().__init__(held_item)
        self.chest_index = chest_index

    # Unlike script-based treasures, the ChestTreasure actually writes the
    # changes directly to the rom.
    def write_to_ctrom(self, ctrom: CTRom):
        fsrom = ctrom.rom_data
        fsrom.seek(ChestTreasure.treasure_ptr+4*self.chest_index + 2)

        # write two bytes to clear the gold/empty flags
        ctrom.rom_data.write(to_little_endian(self.held_item, 2))


# Treasures that are obtained by the script adding it to your inventory
class ScriptTreasure(Treasure):

    def __init__(self, location: LocID, object_id: int, function_id: int,
                 held_item: ItemID = ItemID.MOP, item_num=0):
        super().__init__(held_item)
        self.location = location
        self.object_id = object_id
        self.function_id = function_id
        self.item_num = item_num

    def __repr__(self):
        x = (
            f"{type(self).__name__}(location={self.location}, " +
            f"object_id={self.object_id}, function_id={self.function_id},  " +
            f"held_item={self.held_item}, "
            f"item_num={self.item_num})"
        )
        return x

    def write_to_ctrom(self, ctrom: CTRom):

        script_manager = ctrom.script_manager
        script = script_manager.get_script(self.location)

        pos = script.get_function_start(self.object_id,
                                        self.function_id)
        end = script.get_function_end(self.object_id,
                                      self.function_id)

        num_add_item = 0
        num_set_item_mem = 0

        # 0x4F is setting memory, 0xCA is adding item
        cmd_ids = [0x4F, 0xCA]

        # Loop until we find exactly the right number of item display and
        # item add commands
        while (num_add_item != self.item_num+1 or
               num_set_item_mem != self.item_num+1):

            pos, cmd = script.find_command(cmd_ids, pos, end)

            if pos is None:
                print('Error setting item:\n\t', end='')
                print(self)
                exit()

            if cmd.command == 0x4F:
                # Item text location is 0x7F0200.  In the command, this is
                # the last argument.
                if cmd.args[-1] != 0x00:
                    continue
                else:
                    num_set_item_mem += 1
                    set_item_mem_addr = pos + 2  # cmd, val, mem
            elif cmd.command == 0xCA:
                num_add_item += 1
                add_item_addr = pos + 1  # cmd, item

            pos += len(cmd)

        script.data[set_item_mem_addr] = int(self.held_item)
        script.data[add_item_addr] = int(self.held_item)


class RandoConfig:

    def __init__(self, rom: bytearray):

        self.treasure_assign_dict = {
            TID.TRUCE_MAYOR_1F: ChestTreasure(0x02),
            TID.TRUCE_MAYOR_2F: ChestTreasure(0x03),
            TID.KINGS_ROOM_1000: ChestTreasure(0x04),
            TID.QUEENS_ROOM_1000: ChestTreasure(0x05),
            TID.GUARDIA_BASEMENT_1: ChestTreasure(0x06),
            TID.GUARDIA_BASEMENT_2: ChestTreasure(0x07),
            TID.GUARDIA_BASEMENT_3: ChestTreasure(0x08),
            # non-cs
            TID.GUARDIA_JAIL_FRITZ_STORAGE: ChestTreasure(0x09),
            # end non-cs
            TID.FOREST_RUINS: ChestTreasure(0x0A),
            TID.HECKRAN_CAVE_SIDETRACK: ChestTreasure(0x0B),
            TID.HECKRAN_CAVE_ENTRANCE: ChestTreasure(0x0C),
            TID.HECKRAN_CAVE_1: ChestTreasure(0x0D),
            TID.HECKRAN_CAVE_2: ChestTreasure(0x0E),
            TID.PORRE_MAYOR_2F: ChestTreasure(0x0F),
            # non-cs
            TID.GUARDIA_JAIL_CELL: ChestTreasure(0x10),
            TID.GUARDIA_JAIL_OMNICRONE_1: ChestTreasure(0x11),
            TID.GUARDIA_JAIL_OMNICRONE_2: ChestTreasure(0x12),
            TID.GUARDIA_JAIL_OMNICRONE_3: ChestTreasure(0x13),
            TID.GUARDIA_JAIL_HOLE_1: ChestTreasure(0x14),
            TID.GUARDIA_JAIL_HOLE_2: ChestTreasure(0x15),
            TID.GUARDIA_JAIL_OUTER_WALL: ChestTreasure(0x16),
            TID.GUARDIA_JAIL_OMNICRONE_4: ChestTreasure(0x17),
            TID.GUARDIA_JAIL_FRITZ: ChestTreasure(0x18),
            # end non-cs
            TID.GIANTS_CLAW_KINO_CELL: ChestTreasure(0x19),
            TID.GIANTS_CLAW_TRAPS: ChestTreasure(0x1A),
            TID.TRUCE_CANYON_1: ChestTreasure(0x1B),
            TID.TRUCE_CANYON_2: ChestTreasure(0x1C),
            TID.KINGS_ROOM_600: ChestTreasure(0x1D),
            TID.QUEENS_ROOM_600: ChestTreasure(0x1E),
            TID.ROYAL_KITCHEN: ChestTreasure(0x1F),
            # non-cs
            TID.MAGUS_CASTLE_RIGHT_HALL: ChestTreasure(0x20),
            # end non-cs
            TID.MANORIA_CATHEDRAL_1: ChestTreasure(0x21),
            TID.MANORIA_CATHEDRAL_2: ChestTreasure(0x22),
            TID.MANORIA_CATHEDRAL_3: ChestTreasure(0x23),
            TID.MANORIA_INTERIOR_1: ChestTreasure(0x24),
            TID.MANORIA_INTERIOR_2: ChestTreasure(0x25),
            TID.MANORIA_INTERIOR_3: ChestTreasure(0x26),
            TID.MANORIA_INTERIOR_4: ChestTreasure(0x27),
            TID.CURSED_WOODS_1: ChestTreasure(0x28),
            TID.CURSED_WOODS_2: ChestTreasure(0x29),
            TID.FROGS_BURROW_RIGHT: ChestTreasure(0x2A),
            TID.DENADORO_MTS_SCREEN2_1: ChestTreasure(0x2B),
            TID.DENADORO_MTS_SCREEN2_2: ChestTreasure(0x2C),
            TID.DENADORO_MTS_SCREEN2_3: ChestTreasure(0x2D),
            TID.DENADORO_MTS_FINAL_1: ChestTreasure(0x2E),
            TID.DENADORO_MTS_FINAL_2: ChestTreasure(0x2F),
            TID.DENADORO_MTS_FINAL_3: ChestTreasure(0x30),
            TID.DENADORO_MTS_WATERFALL_TOP_1: ChestTreasure(0x31),
            TID.DENADORO_MTS_WATERFALL_TOP_2: ChestTreasure(0x32),
            TID.DENADORO_MTS_WATERFALL_TOP_3: ChestTreasure(0x33),
            TID.DENADORO_MTS_WATERFALL_TOP_4: ChestTreasure(0x34),
            TID.DENADORO_MTS_WATERFALL_TOP_5: ChestTreasure(0x35),
            TID.DENADORO_MTS_ENTRANCE_1: ChestTreasure(0x36),
            TID.DENADORO_MTS_ENTRANCE_2: ChestTreasure(0x37),
            TID.DENADORO_MTS_SCREEN3_1: ChestTreasure(0x38),
            TID.DENADORO_MTS_SCREEN3_2: ChestTreasure(0x39),
            TID.DENADORO_MTS_SCREEN3_3: ChestTreasure(0x3A),
            TID.DENADORO_MTS_SCREEN3_4: ChestTreasure(0x3B),
            TID.DENADORO_MTS_AMBUSH: ChestTreasure(0x3C),
            TID.DENADORO_MTS_SAVE_PT: ChestTreasure(0x3D),
            TID.FIONAS_HOUSE_1: ChestTreasure(0x3E),
            TID.FIONAS_HOUSE_2: ChestTreasure(0x3F),
            # Block of non-Chronosanity chests
            TID.SUNKEN_DESERT_B1_NW: ChestTreasure(0x40),
            TID.SUNKEN_DESERT_B1_NE: ChestTreasure(0x41),
            TID.SUNKEN_DESERT_B1_SE: ChestTreasure(0x42),
            TID.SUNKEN_DESERT_B1_SW: ChestTreasure(0x43),
            TID.SUNKEN_DESERT_B2_NW: ChestTreasure(0x44),
            TID.SUNKEN_DESERT_B2_N: ChestTreasure(0x45),
            TID.SUNKEN_DESERT_B2_W: ChestTreasure(0x46),
            TID.SUNKEN_DESERT_B2_SW: ChestTreasure(0x47),
            TID.SUNKEN_DESERT_B2_SE: ChestTreasure(0x48),
            TID.SUNKEN_DESERT_B2_E: ChestTreasure(0x49),
            TID.SUNKEN_DESERT_B2_CENTER: ChestTreasure(0x4A),
            TID.MAGUS_CASTLE_GUILLOTINE_1: ChestTreasure(0x4B),
            TID.MAGUS_CASTLE_GUILLOTINE_2: ChestTreasure(0x4C),
            TID.MAGUS_CASTLE_SLASH_ROOM_1: ChestTreasure(0x4D),
            TID.MAGUS_CASTLE_SLASH_ROOM_2: ChestTreasure(0x4E),
            TID.MAGUS_CASTLE_STATUE_HALL: ChestTreasure(0x4F),
            TID.MAGUS_CASTLE_FOUR_KIDS: ChestTreasure(0x50),
            TID.MAGUS_CASTLE_OZZIE_1: ChestTreasure(0x51),
            TID.MAGUS_CASTLE_OZZIE_2: ChestTreasure(0x52),
            TID.MAGUS_CASTLE_ENEMY_ELEVATOR: ChestTreasure(0x53),
            # end non-CS block
            TID.OZZIES_FORT_GUILLOTINES_1: ChestTreasure(0x54),
            TID.OZZIES_FORT_GUILLOTINES_2: ChestTreasure(0x55),
            TID.OZZIES_FORT_GUILLOTINES_3: ChestTreasure(0x56),
            TID.OZZIES_FORT_GUILLOTINES_4: ChestTreasure(0x57),
            TID.OZZIES_FORT_FINAL_1: ChestTreasure(0x58),
            TID.OZZIES_FORT_FINAL_2: ChestTreasure(0x59),
            TID.GIANTS_CLAW_CAVES_1: ChestTreasure(0x5A),
            TID.GIANTS_CLAW_CAVES_2: ChestTreasure(0x5B),
            TID.GIANTS_CLAW_CAVES_3: ChestTreasure(0x5C),
            TID.GIANTS_CLAW_CAVES_4: ChestTreasure(0x5D),
            TID.GIANTS_CLAW_ROCK: ChestTreasure(0x5E),
            TID.GIANTS_CLAW_CAVES_5: ChestTreasure(0x5F),
            TID.YAKRAS_ROOM: ChestTreasure(0x60),
            TID.MANORIA_SHRINE_SIDEROOM_1: ChestTreasure(0x61),
            TID.MANORIA_SHRINE_SIDEROOM_2: ChestTreasure(0x62),
            TID.MANORIA_BROMIDE_1: ChestTreasure(0x63),
            TID.MANORIA_BROMIDE_2: ChestTreasure(0x64),
            TID.MANORIA_BROMIDE_3: ChestTreasure(0x65),
            TID.MANORIA_SHRINE_MAGUS_1: ChestTreasure(0x66),
            TID.MANORIA_SHRINE_MAGUS_2: ChestTreasure(0x67),
            TID.BANGOR_DOME_SEAL_1: ChestTreasure(0x68),
            TID.BANGOR_DOME_SEAL_2: ChestTreasure(0x69),
            TID.BANGOR_DOME_SEAL_3: ChestTreasure(0x6A),
            TID.TRANN_DOME_SEAL_1: ChestTreasure(0x6B),
            TID.TRANN_DOME_SEAL_2: ChestTreasure(0x6C),
            TID.LAB_16_1: ChestTreasure(0x6D),
            TID.LAB_16_2: ChestTreasure(0x6E),
            TID.LAB_16_3: ChestTreasure(0x6F),
            TID.LAB_16_4: ChestTreasure(0x70),
            TID.ARRIS_DOME_RATS: ChestTreasure(0x71),
            TID.ARRIS_DOME_SEAL_1: ChestTreasure(0x72),
            TID.ARRIS_DOME_SEAL_2: ChestTreasure(0x73),
            TID.ARRIS_DOME_SEAL_3: ChestTreasure(0x74),
            TID.ARRIS_DOME_SEAL_4: ChestTreasure(0x75),
            # Non-CS
            TID.REPTITE_LAIR_SECRET_B2_NE_RIGHT: ChestTreasure(0x76),
            #
            TID.LAB_32_1: ChestTreasure(0x77),
            # Non-CS
            TID.LAB_32_RACE_LOG: ChestTreasure(0x78),
            # end non-cs
            TID.FACTORY_LEFT_AUX_CONSOLE: ChestTreasure(0x79),
            TID.FACTORY_LEFT_SECURITY_RIGHT: ChestTreasure(0x7A),
            TID.FACTORY_LEFT_SECURITY_LEFT: ChestTreasure(0x7B),
            TID.FACTORY_RIGHT_FLOOR_TOP: ChestTreasure(0x7C),
            TID.FACTORY_RIGHT_FLOOR_LEFT: ChestTreasure(0x7D),
            TID.FACTORY_RIGHT_FLOOR_BOTTOM: ChestTreasure(0x7E),
            TID.FACTORY_RIGHT_FLOOR_SECRET: ChestTreasure(0x7F),
            TID.FACTORY_RIGHT_CRANE_LOWER: ChestTreasure(0x80),
            TID.FACTORY_RIGHT_CRANE_UPPER: ChestTreasure(0x81),
            TID.FACTORY_RIGHT_INFO_ARCHIVE: ChestTreasure(0x82),
            # Non-CS
            TID.FACTORY_RUINS_GENERATOR: ChestTreasure(0x83),
            # end non-cs
            TID.SEWERS_1: ChestTreasure(0x84),
            TID.SEWERS_2: ChestTreasure(0x85),
            TID.SEWERS_3: ChestTreasure(0x86),
            # Non-CS
            TID.DEATH_PEAK_SOUTH_FACE_KRAKKER: ChestTreasure(0x87),
            TID.DEATH_PEAK_SOUTH_FACE_SPAWN_SAVE: ChestTreasure(0x88),
            TID.DEATH_PEAK_SOUTH_FACE_SUMMIT: ChestTreasure(0x89),
            TID.DEATH_PEAK_FIELD: ChestTreasure(0x8A),
            # End Non-CS block
            TID.GENO_DOME_1F_1: ChestTreasure(0x8B),
            TID.GENO_DOME_1F_2: ChestTreasure(0x8C),
            TID.GENO_DOME_1F_3: ChestTreasure(0x8D),
            TID.GENO_DOME_1F_4: ChestTreasure(0x8E),
            TID.GENO_DOME_ROOM_1: ChestTreasure(0x8F),
            TID.GENO_DOME_ROOM_2: ChestTreasure(0x90),
            TID.GENO_DOME_PROTO4_1: ChestTreasure(0x91),
            TID.GENO_DOME_PROTO4_2: ChestTreasure(0x92),
            TID.FACTORY_RIGHT_DATA_CORE_1: ChestTreasure(0x93),
            TID.FACTORY_RIGHT_DATA_CORE_2: ChestTreasure(0x94),
            # Non-CS
            TID.DEATH_PEAK_KRAKKER_PARADE: ChestTreasure(0x95),
            TID.DEATH_PEAK_CAVES_LEFT: ChestTreasure(0x96),
            TID.DEATH_PEAK_CAVES_CENTER: ChestTreasure(0x97),
            TID.DEATH_PEAK_CAVES_RIGHT: ChestTreasure(0x98),
            # End Non-CS block
            TID.GENO_DOME_2F_1: ChestTreasure(0x99),
            TID.GENO_DOME_2F_2: ChestTreasure(0x9A),
            TID.GENO_DOME_2F_3: ChestTreasure(0x9B),
            TID.GENO_DOME_2F_4: ChestTreasure(0x9C),
            TID.MYSTIC_MT_STREAM: ChestTreasure(0x9D),
            TID.FOREST_MAZE_1: ChestTreasure(0x9E),
            TID.FOREST_MAZE_2: ChestTreasure(0x9F),
            TID.FOREST_MAZE_3: ChestTreasure(0xA0),
            TID.FOREST_MAZE_4: ChestTreasure(0xA1),
            TID.FOREST_MAZE_5: ChestTreasure(0xA2),
            TID.FOREST_MAZE_6: ChestTreasure(0xA3),
            TID.FOREST_MAZE_7: ChestTreasure(0xA4),
            TID.FOREST_MAZE_8: ChestTreasure(0xA5),
            TID.FOREST_MAZE_9: ChestTreasure(0xA6),
            # Non-CS
            TID.REPTITE_LAIR_SECRET_B1_SW: ChestTreasure(0xA7),
            TID.REPTITE_LAIR_SECRET_B1_NE: ChestTreasure(0xA8),
            TID.REPTITE_LAIR_SECRET_B1_SE: ChestTreasure(0xA9),
            TID.REPTITE_LAIR_SECRET_B2_SE_RIGHT: ChestTreasure(0xAA),
            TID.REPTITE_LAIR_SECRET_B2_NE_OR_SE_LEFT: ChestTreasure(0xAB),
            TID.REPTITE_LAIR_SECRET_B2_SW: ChestTreasure(0xAC),
            # End non-CS block
            TID.REPTITE_LAIR_REPTITES_1: ChestTreasure(0xAD),
            TID.REPTITE_LAIR_REPTITES_2: ChestTreasure(0xAE),
            TID.DACTYL_NEST_1: ChestTreasure(0xAF),
            TID.DACTYL_NEST_2: ChestTreasure(0xB0),
            TID.DACTYL_NEST_3: ChestTreasure(0xB1),
            # Non-CS
            TID.GIANTS_CLAW_THRONE_1: ChestTreasure(0xB2),
            TID.GIANTS_CLAW_THRONE_2: ChestTreasure(0xB3),
            # TYRANO_LAIR_THRONE: 0xB4 (Unused?)
            TID.TYRANO_LAIR_TRAPDOOR: ChestTreasure(0xB5),
            TID.TYRANO_LAIR_KINO_CELL: ChestTreasure(0xB6),
            # TYRANO_LAIR Unused? : 0xB7
            TID.TYRANO_LAIR_MAZE_1: ChestTreasure(0xB8),
            TID.TYRANO_LAIR_MAZE_2: ChestTreasure(0xB9),
            TID.TYRANO_LAIR_MAZE_3: ChestTreasure(0xBA),
            TID.TYRANO_LAIR_MAZE_4: ChestTreasure(0xBB),
            # 0xBC - 0xCF - BLACK_OMEN
            TID.BLACK_OMEN_AUX_COMMAND_MID: ChestTreasure(0xBC),
            TID.BLACK_OMEN_AUX_COMMAND_NE: ChestTreasure(0xBD),
            TID.BLACK_OMEN_GRAND_HALL: ChestTreasure(0xBE),
            TID.BLACK_OMEN_NU_HALL_NW: ChestTreasure(0xBF),
            TID.BLACK_OMEN_NU_HALL_W: ChestTreasure(0xC0),
            TID.BLACK_OMEN_NU_HALL_SW: ChestTreasure(0xC1),
            TID.BLACK_OMEN_NU_HALL_NE: ChestTreasure(0xC2),
            TID.BLACK_OMEN_NU_HALL_E: ChestTreasure(0xC3),
            TID.BLACK_OMEN_NU_HALL_SE: ChestTreasure(0xC4),
            TID.BLACK_OMEN_ROYAL_PATH: ChestTreasure(0xC5),
            TID.BLACK_OMEN_RUMINATOR_PARADE: ChestTreasure(0xC6),
            TID.BLACK_OMEN_EYEBALL_HALL: ChestTreasure(0xC7),
            TID.BLACK_OMEN_TUBSTER_FLY: ChestTreasure(0xC8),
            TID.BLACK_OMEN_MARTELLO: ChestTreasure(0xC9),
            TID.BLACK_OMEN_ALIEN_SW: ChestTreasure(0xCA),
            TID.BLACK_OMEN_ALIEN_NE: ChestTreasure(0xCB),
            TID.BLACK_OMEN_ALIEN_NW: ChestTreasure(0xCC),
            TID.BLACK_OMEN_TERRA_W: ChestTreasure(0xCD),
            TID.BLACK_OMEN_TERRA_ROCK: ChestTreasure(0xCE),
            TID.BLACK_OMEN_TERRA_NE: ChestTreasure(0xCF),
            # end non-cs
            TID.ARRIS_DOME_FOOD_STORE: ChestTreasure(0xD0),
            TID.MT_WOE_2ND_SCREEN_1: ChestTreasure(0xD1),
            TID.MT_WOE_2ND_SCREEN_2: ChestTreasure(0xD2),
            TID.MT_WOE_2ND_SCREEN_3: ChestTreasure(0xD3),
            TID.MT_WOE_2ND_SCREEN_4: ChestTreasure(0xD4),
            TID.MT_WOE_2ND_SCREEN_5: ChestTreasure(0xD5),
            TID.MT_WOE_3RD_SCREEN_1: ChestTreasure(0xD6),
            TID.MT_WOE_3RD_SCREEN_2: ChestTreasure(0xD7),
            TID.MT_WOE_3RD_SCREEN_3: ChestTreasure(0xD8),
            TID.MT_WOE_3RD_SCREEN_4: ChestTreasure(0xD9),
            TID.MT_WOE_3RD_SCREEN_5: ChestTreasure(0xDA),
            TID.MT_WOE_1ST_SCREEN: ChestTreasure(0xDB),
            TID.MT_WOE_FINAL_1: ChestTreasure(0xDC),
            TID.MT_WOE_FINAL_2: ChestTreasure(0xDD),
            # Non-cs
            TID.OCEAN_PALACE_MAIN_S: ChestTreasure(0xDE),
            TID.OCEAN_PALACE_MAIN_N: ChestTreasure(0xDF),
            TID.OCEAN_PALACE_E_ROOM: ChestTreasure(0xE0),
            TID.OCEAN_PALACE_W_ROOM: ChestTreasure(0xE1),
            TID.OCEAN_PALACE_SWITCH_NW: ChestTreasure(0xE2),
            TID.OCEAN_PALACE_SWITCH_SW: ChestTreasure(0xE3),
            TID.OCEAN_PALACE_SWITCH_NE: ChestTreasure(0xE4),
            TID.OCEAN_PALACE_SWITCH_SECRET: ChestTreasure(0xE5),
            TID.OCEAN_PALACE_FINAL: ChestTreasure(0xE6),
            # end non-cs
            # FACTORY_RUINS_UNUSED: 0xE7
            TID.GUARDIA_TREASURY_1: ChestTreasure(0xE8),
            TID.GUARDIA_TREASURY_2: ChestTreasure(0xE9),
            TID.GUARDIA_TREASURY_3: ChestTreasure(0xEA),
            TID.QUEENS_TOWER_600: ChestTreasure(0xEB),
            # Non-cs block
            TID.MAGUS_CASTLE_LEFT_HALL: ChestTreasure(0xEC),
            TID.MAGUS_CASTLE_UNSKIPPABLES: ChestTreasure(0xED),
            TID.MAGUS_CASTLE_PIT_E: ChestTreasure(0xEE),
            TID.MAGUS_CASTLE_PIT_NE: ChestTreasure(0xEF),
            TID.MAGUS_CASTLE_PIT_NW: ChestTreasure(0xF0),
            TID.MAGUS_CASTLE_PIT_W: ChestTreasure(0xF1),
            # end non-cs
            TID.KINGS_TOWER_600: ChestTreasure(0xF2),
            TID.KINGS_TOWER_1000: ChestTreasure(0xF3),
            TID.QUEENS_TOWER_1000: ChestTreasure(0xF4),
            TID.GUARDIA_COURT_TOWER: ChestTreasure(0xF5),
            TID.PRISON_TOWER_1000: ChestTreasure(0xF6),
            # GIANTS_CLAW_MAZE Unused: 0xF7
            # DEATH_PEAK_CLIFF Unused: 0xF8
            # Script Chests:
            # Weirdness with Northern Ruins.
            # There's a variable set, only for these
            # locations indicating whether you're in the
            #   0x7F10A3 & 0x10 ->  600
            #   0x7F10A3 & 0x20 -> 1000
            TID.NORTHERN_RUINS_BASEMENT_600: ScriptTreasure(
                location=LocID.NORTHERN_RUINS_BASEMENT,
                object_id=0x08,
                function_id=0x01,
                item_num=1
            ),
            # Frog locked one
            TID.NORTHERN_RUINS_BASEMENT_1000: ScriptTreasure(
                location=LocID.NORTHERN_RUINS_BASEMENT,
                object_id=0x08,
                function_id=0x01,
                item_num=0
            ),
            TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_1000: ScriptTreasure(
                location=LocID.NORTHERN_RUINS_ANTECHAMBER,
                object_id=0x08,
                function_id=0x01,
                item_num=0
            ),
            TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_600: ScriptTreasure(
                location=LocID.NORTHERN_RUINS_ANTECHAMBER,
                object_id=0x08,
                function_id=0x01,
                item_num=1
            ),
            TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_1000: ScriptTreasure(
                location=LocID.NORTHERN_RUINS_ANTECHAMBER,
                object_id=0x10,
                function_id=0x01,
                item_num=0
            ),
            TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_600: ScriptTreasure(
                location=LocID.NORTHERN_RUINS_ANTECHAMBER,
                object_id=0x10,
                function_id=0x01,
                item_num=1
            ),
            TID.NORTHERN_RUINS_BACK_LEFT_SEALED_1000: ScriptTreasure(
                location=LocID.NORTHERN_RUINS_BACK_ROOM,
                object_id=0x10,
                function_id=0x01,
                item_num=0
            ),
            TID.NORTHERN_RUINS_BACK_LEFT_SEALED_600: ScriptTreasure(
                location=LocID.NORTHERN_RUINS_ANTECHAMBER,
                object_id=0x10,
                function_id=0x01,
                item_num=1
            ),
            TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_1000: ScriptTreasure(
                location=LocID.NORTHERN_RUINS_BACK_ROOM,
                object_id=0x11,
                function_id=0x01,
                item_num=0
            ),
            TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_600: ScriptTreasure(
                location=LocID.NORTHERN_RUINS_ANTECHAMBER,
                object_id=0x11,
                function_id=0x01,
                item_num=1
            ),
            TID.TRUCE_INN_SEALED_600: ScriptTreasure(
                location=LocID.TRUCE_INN_600_2F,
                object_id=0x0C,
                function_id=0,
            ),
            TID.TRUCE_INN_SEALED_1000: ScriptTreasure(
                location=LocID.TRUCE_INN_1000,
                object_id=0x11,
                function_id=0x01
            ),
            TID.PYRAMID_LEFT: ScriptTreasure(
                location=LocID.FOREST_RUINS,
                object_id=0x13,
                function_id=0x01
            ),
            TID.PYRAMID_RIGHT: ScriptTreasure(
                location=LocID.FOREST_RUINS,
                object_id=0x14,
                function_id=0x01
            ),
            TID.PORRE_ELDER_SEALED_1: ScriptTreasure(
                location=LocID.PORRE_ELDER,
                object_id=0x0D,
                function_id=0x01
            ),
            TID.PORRE_ELDER_SEALED_2: ScriptTreasure(
                location=LocID.PORRE_ELDER,
                object_id=0x0E,
                function_id=0x01
            ),
            TID.PORRE_MAYOR_SEALED_1: ScriptTreasure(
                location=LocID.PORRE_MAYOR_2F,
                object_id=0x09,
                function_id=0x01
            ),
            TID.PORRE_MAYOR_SEALED_2: ScriptTreasure(
                location=LocID.PORRE_MAYOR_2F,
                object_id=0x0A,
                function_id=0x01
            ),
            TID.GUARDIA_CASTLE_SEALED_600: ScriptTreasure(
                location=LocID.GUARDIA_CASTLE_KINGS_TOWER_600,
                object_id=0x08,
                function_id=0x01
            ),
            TID.GUARDIA_FOREST_SEALED_600: ScriptTreasure(
                location=LocID.GUARDIA_FOREST_600,
                object_id=0x3E,
                function_id=0x01
            ),
            TID.GUARDIA_FOREST_SEALED_1000: ScriptTreasure(
                location=LocID.GUARDIA_FOREST_DEAD_END,
                object_id=0x12,
                function_id=0x01
            ),
            TID.GUARDIA_CASTLE_SEALED_1000: ScriptTreasure(
                location=LocID.GUARDIA_CASTLE_KINGS_TOWER_1000,
                object_id=0x08,
                function_id=0x01
            ),
            TID.HECKRAN_SEALED_1: ScriptTreasure(
                location=LocID.HECKRAN_CAVE_PASSAGEWAYS,
                object_id=0x0C,
                function_id=0x01,
                item_num=0
            ),
            TID.HECKRAN_SEALED_2: ScriptTreasure(
                location=LocID.HECKRAN_CAVE_PASSAGEWAYS,
                object_id=0x0C,
                function_id=0x01,
                item_num=1
            ),
            TID.MAGIC_CAVE_SEALED: ScriptTreasure(
                location=LocID.MAGIC_CAVE_INTERIOR,
                object_id=0x19,
                function_id=0x01
            ),
            # Key Items
            TID.REPTITE_LAIR_KEY: ScriptTreasure(
                LocID.REPTITE_LAIR_AZALA_ROOM,
                object_id=0x00,
                function_id=0x00
            ),
            TID.MELCHIOR_KEY: ScriptTreasure(
                location=LocID.GUARDIA_REAR_STORAGE,
                object_id=0x17,
                function_id=0x1
            ),
            TID.FROGS_BURROW_LEFT: ScriptTreasure(location=LocID.FROGS_BURROW,
                                                  object_id=0x0A,
                                                  function_id=0x01),
            TID.MT_WOE_KEY: ScriptTreasure(location=LocID.MT_WOE_SUMMIT,
                                           object_id=0x08,
                                           function_id=0x01),
            TID.FIONA_KEY: ScriptTreasure(location=LocID.FIONAS_SHRINE,
                                          object_id=0x08,
                                          function_id=0x03),
            TID.ARRIS_DOME_KEY: ScriptTreasure(location=LocID.ARRIS_DOME,
                                               object_id=0x0F,
                                               function_id=0x2),
            TID.SUN_PALACE_KEY: ScriptTreasure(location=LocID.SUN_PALACE,
                                               object_id=0x11,
                                               function_id=0x01),
            TID.GENO_DOME_KEY: ScriptTreasure(
                location=LocID.GENO_DOME_MAINFRAME,
                object_id=0x01,
                function_id=0x04
            ),
            TID.GIANTS_CLAW_KEY: ScriptTreasure(
                location=LocID.GIANTS_CLAW_TYRANO,
                object_id=0x0A,
                function_id=0x01
            ),
            TID.KINGS_TRIAL_KEY: ScriptTreasure(
                location=LocID.GUARDIA_REAR_STORAGE,
                object_id=0x02,
                function_id=0x03
            ),
            TID.ZENAN_BRIDGE_KEY: ScriptTreasure(LocID.GUARDIA_THRONEROOM_600,
                                                 object_id=0x0F,
                                                 function_id=0x00),
            TID.SNAIL_STOP_KEY: ScriptTreasure(LocID.SNAIL_STOP,
                                               object_id=0x09,
                                               function_id=0x01),
            TID.LAZY_CARPENTER: ScriptTreasure(LocID.CHORAS_CARPENTER_1000,
                                               object_id=0x08,
                                               function_id=0x01),
            TID.TABAN_KEY: ScriptTreasure(LocID.LUCCAS_WORKSHOP,
                                          object_id=0x08,
                                          function_id=0x01,
                                          item_num=0),
            TID.DENADORO_MTS_KEY: ScriptTreasure(
                location=LocID.CAVE_OF_MASAMUNE,
                object_id=0x0A,
                function_id=0x2
            ),
            # Other Script Treasures
            TID.TABAN_GIFT_HELM: ScriptTreasure(LocID.LUCCAS_WORKSHOP,
                                                object_id=0x08,
                                                function_id=0x01,
                                                item_num=1),
            TID.TABAN_GIFT_WEAPON: ScriptTreasure(LocID.LUCCAS_WORKSHOP,
                                                  object_id=0x08,
                                                  function_id=0x01,
                                                  item_num=2),
            TID.TRADING_POST_RANGED_WEAPON: ScriptTreasure(
                location=LocID.IOKA_TRADING_POST,
                object_id=0x0C,
                function_id=0x03,
                item_num=0
            ),
            TID.TRADING_POST_ACCESSORY: ScriptTreasure(
                location=LocID.IOKA_TRADING_POST,
                object_id=0x0C,
                function_id=0x03,
                item_num=1
            ),
            TID.TRADING_POST_TAB: ScriptTreasure(
                location=LocID.IOKA_TRADING_POST,
                object_id=0x0C,
                function_id=0x03,
                item_num=2
            ),
            TID.TRADING_POST_MELEE_WEAPON: ScriptTreasure(
                location=LocID.IOKA_TRADING_POST,
                object_id=0x0C,
                function_id=0x03,
                item_num=3
            ),
            TID.TRADING_POST_ARMOR: ScriptTreasure(
                location=LocID.IOKA_TRADING_POST,
                object_id=0x0C,
                function_id=0x03,
                item_num=4
            ),
            TID.TRADING_POST_HELM: ScriptTreasure(
                location=LocID.IOKA_TRADING_POST,
                object_id=0x0C,
                function_id=0x03,
                item_num=5
            ),
            TID.JERKY_GIFT: ScriptTreasure(
                location=LocID.PORRE_MAYOR_1F,
                object_id=0x08,
                function_id=0x01,
                item_num=0
            ),
            TID.DENADORO_ROCK: ScriptTreasure(
                location=LocID.DENADORO_MTS_MASAMUNE_EXTERIOR,
                object_id=0x01,
                function_id=0x07
            ),
            TID.LARUBA_ROCK: ScriptTreasure(
                location=LocID.LARUBA_RUINS,
                object_id=0x0D,
                function_id=0x01
            ),
            TID.KAJAR_ROCK: ScriptTreasure(
                location=LocID.KAJAR_ROCK_ROOM,
                object_id=0x08,
                function_id=0x01
            )
            # Tabs later if they're going to be randomized
            # GUARDIA_FOREST_POWER_TAB_600: auto()
            # GUARDIA_FOREST_POWER_TAB_1000: auto()
            # SUN_KEEP_POWER_TAB_600: auto()
            # MEDINA_ELDER_SPEED_TAB: auto()
            # MEDINA_ELDER_MAGIC_TAB: auto()
        }

        # char assignments are completely arbitrary here
        # the keys can be different since there's some redundancy in the
        # key and the arg to CharRecruit
        self.char_assign_dict = {
            RecruitID.STARTER_1: StarterChar(
                held_char=CharID.CRONO,
                starter_num=0  # A little bothered by the 0 vs 1 here
            ),
            RecruitID.STARTER_2: StarterChar(
                held_char=CharID.MAGUS,
                starter_num=1
            ),
            RecruitID.CATHEDRAL: CharRecruit(
                held_char=CharID.LUCCA,
                loc_id=LocID.MANORIA_SANCTUARY,
                load_obj_id=0x19,
                recruit_obj_id=0x19
            ),
            RecruitID.CASTLE: CharRecruit(
                held_char=CharID.MARLE,
                loc_id=LocID.GUARDIA_QUEENS_CHAMBER_600,
                load_obj_id=0x17,
                recruit_obj_id=0x18
            ),
            RecruitID.FROGS_BURROW: CharRecruit(
                held_char=CharID.FROG,
                loc_id=LocID.FROGS_BURROW,
                load_obj_id=0x0F,
                recruit_obj_id=0x0F
            ),
            RecruitID.DACTYL_NEST: CharRecruit(
                held_char=CharID.AYLA,
                loc_id=LocID.DACTYL_NEST_SUMMIT,
                load_obj_id=0x0D,
                recruit_obj_id=0x0D
            ),
            RecruitID.PROTO_DOME: CharRecruit(
                held_char=CharID.ROBO,
                loc_id=LocID.PROTO_DOME,
                load_obj_id=0x18,
                recruit_obj_id=0x18
            )
        }

        self.boss_assign_dict = {
            LocID.PRISON_CATWALKS: BossID.DRAGON_TANK,
            LocID.FACTORY_RUINS_SECURITY_CENTER: BossID.R_SERIES,
            LocID.BLACK_OMEN_ELDER_SPAWN: BossID.ELDER_SPAWN,
            LocID.MAGUS_CASTLE_FLEA: BossID.FLEA,
            LocID.OZZIES_FORT_FLEA_PLUS: BossID.FLEA_PLUS,
            LocID.MT_WOE_SUMMIT: BossID.GIGA_GAIA,
            LocID.BLACK_OMEN_GIGA_MUTANT: BossID.GIGA_MUTANT,
            LocID.ZEAL_PALACE_THRONE_NIGHT: BossID.GOLEM,
            LocID.ARRIS_DOME_GUARDIAN_CHAMBER: BossID.GUARDIAN,
            LocID.HECKRAN_CAVE_NEW: BossID.HECKRAN,
            LocID.DEATH_PEAK_GUARDIAN_SPAWN: BossID.LAVOS_SPAWN,
            LocID.CAVE_OF_MASAMUNE: BossID.MASA_MUNE,
            LocID.GENO_DOME_MAINFRAME: BossID.MOTHER_BRAIN,
            LocID.REPTITE_LAIR_AZALA_ROOM: BossID.NIZBEL,
            LocID.TYRANO_LAIR_NIZBEL: BossID.NIZBEL_2,
            LocID.SUNKEN_DESERT_DEVOURER: BossID.RETINITE,
            LocID.GIANTS_CLAW_TYRANO: BossID.RUST_TYRANO,
            LocID.MAGUS_CASTLE_SLASH: BossID.SLASH_SWORD,
            LocID.SUN_PALACE: BossID.SON_OF_SUN,
            LocID.OZZIES_FORT_SUPER_SLASH: BossID.SUPER_SLASH,
            LocID.BLACK_OMEN_TERRA_MUTANT: BossID.TERRA_MUTANT,
            LocID.OCEAN_PALACE_TWIN_GOLEM: BossID.TWIN_GOLEM,
            LocID.MANORIA_COMMAND: BossID.YAKRA,
            LocID.KINGS_TRIAL_NEW: BossID.YAKRA_XIII,
            LocID.ZENAN_BRIDGE: BossID.ZOMBOR
        }

        self.boss_data_dict = get_boss_data_dict(rom)
        self.boss_rank = dict()
        self.enemy_dict = enemystats.get_stat_dict(rom)
        self.shop_manager = ShopManager(rom)
        self.price_manager = PriceManager(rom)
        self.char_manager = CharManager(rom)

        self.key_item_locations = []

        self.techdb = techdb.TechDB.get_default_db(rom)

    def write_to_ctrom(self, ctrom: CTRom):
        # Write enemies out
        for enemy_id, stats in self.enemy_dict.items():
            stats.write_to_stream(ctrom.rom_data, enemy_id)

        # Write treasures out
        for treasure in self.treasure_assign_dict.values():
            treasure.write_to_ctrom(ctrom)

        # Write shops out
        self.shop_manager.write_to_ctrom(ctrom)

        # Write prices out
        self.price_manager.write_to_ctrom(ctrom)

        # Write characters out
        # Recruitment spots
        for character in self.char_assign_dict.values():
            character.write_to_ctrom(ctrom)

        # Stats
        self.char_manager.write_stats_to_ctrom(ctrom)

        # TODO: duplicate character assignments
        # TODO: tech rando

    def write_spoiler_log(self, filename):
        with open(filename, 'w') as outfile:
            outfile.write('Treasures:\n')

            for treasure_loc in self.treasure_assign_dict.keys():
                outfile.write(
                    f"{treasure_loc}: "
                    f"{self.treasure_assign_dict[treasure_loc].held_item}\n"
                )

            outfile.write('\n\nShops and Prices:\n')
            outfile.write(f"{self.shop_manager.__str__(self.price_manager)}\n")
            outfile.write('Prices\n')
            outfile.write(f"{self.price_manager}\n")

    def write_to_stream(self, stream: BufferedWriter):

        # Write enemies out
        for key, value in self.enemy_dict.items():
            value.write_to_stream(stream, key)


def main():
    with open('./roms/jets_test.sfc', 'rb') as infile:
        rom = bytearray(infile.read())

    ctrom = CTRom(rom, ignore_checksum=True)
    space_manager = ctrom.rom_data.space_manager

    # Set up some safe free blocks.
    space_manager.mark_block((0, 0x40FFFF),
                             FSWriteType.MARK_USED)
    space_manager.mark_block((0x411007, 0x5B8000),
                             FSWriteType.MARK_FREE)
    config = RandoConfig(rom)

    # Try out PriceManager
    price_manager = PriceManager(rom)

    # Try out ShopManager
    shop_manager = ShopManager(rom)
    shop_manager.set_shop_items(ShopID.MELCHIOR_FAIR,
                                [ItemID.MOP])

    shop_manager.write_to_ctrom(ctrom)
    shop_manager = ShopManager(ctrom.rom_data.getbuffer())

    shop_manager.print_with_prices(price_manager)

    quit()

    cath = config.char_assign_dict[LocID.MANORIA_SANCTUARY]
    cath.held_char = CharID.LUCCA
    cath.write_to_ctrom(ctrom)

    ctrom.write_all_scripts_to_rom()

    with open('./roms/jets_test_out.sfc', 'wb') as outfile:
        ctrom.rom_data.seek(0)
        outfile.write(ctrom.rom_data.read())


if __name__ == '__main__':
    main()
