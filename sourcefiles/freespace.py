# I am fed up with hardcoding write locations.
from __future__ import annotations
from enum import Enum
from io import BytesIO
from typing import Tuple

from byteops import get_value_from_bytes_be  # for ips marker


class FSWriteType(Enum):
    MARK_USED = 0
    MARK_FREE = 1
    NO_MARK = 2


class FreeSpace():
    def __init__(self, num_bytes, is_free):

        self.num_bytes = num_bytes
        self.markers = [0, self.num_bytes]
        self.first_free = is_free

    # Mark a block of the buffer as free/not free depending on is_free.
    # block is a half-open interval [block[0], block[1]) as is Python's way.
    def mark_block(self,
                   block: Tuple[int, int],
                   is_free: FSWriteType):

        if is_free == FSWriteType.NO_MARK:
            return
        else:
            is_free = (is_free == FSWriteType.MARK_FREE)

        # maybe verify block is valid?
        if block[1] <= block[0]:
            print('Error: Block [%d, %d) has nonpositive size. Returning.'
                  % (block[0], block[1]))

        # If the block to mark goes past the end of the file, extend?
        # This should probably throw an error.
        if block[1] > self.markers[-1]:
            print('Warning: block [%6.6X, %6.6X) exceeds EOF. Truncating.'
                  % (block[0], block[1]))
            block = (block[0], self.markers[-1])

        if block[0] < 0:
            print('Warning: block [%6.6X, %6.6X) preceeds 0. Truncating.'
                  % (block[0], block[1]))
            block = (0, block[1])

        left_blk = self.__search(0, len(self.markers)-2, block[0])
        right_blk = self.__search(0, len(self.markers)-2, block[1])

        lc = (left_blk % 2 == 0)
        rc = (right_blk % 2 == 0)

        left_type = (lc == (self.first_free == is_free))
        right_type = (rc == (self.first_free == is_free))

        if left_type:
            # If the left_type matches the type we're marking, then the left
            # endpoint of the block we found will be the start of a block
            start = left_blk
        elif block[0] == self.markers[left_blk]:
            # If the left_type doesn't match, but we're starting at its
            # leftmost point, then we're just extending the previous matching
            # block.
            if left_blk != 0:  # Unless we're already at the start.
                start = left_blk-1
            else:
                # When at the start, theen just start at the beginning
                start = 0

                # Now the first block's type changes to is_free
                self.first_free = is_free
        else:
            # cut a block
            self.markers.insert(left_blk+1, block[0])
            start = left_blk+1
            right_blk += 1

        if right_type:
            # If the right_type matches, then just extend that block
            end = right_blk+1
        elif block[1] == self.markers[right_blk+1]:
            # If it doesn't match, but it's at the very end of the block,
            # then extend through the next matching block.
            if right_blk+2 == len(self.markers):  # Unless we're at the end_grp
                end = right_blk+1
            else:
                end = right_blk+2
        else:
            # cut the block
            self.markers.insert(right_blk+1, block[1])
            end = right_blk+1

        # delete all markers between the start and the end (not inclusive)
        if end > start+1:
            del(self.markers[start+1:end])
    # End of mark_block

    def extend_end_marker(self, new_end, is_free):
        last_free = self.__is_free(len(self.markers)-2)

        # print(f"{new_end:06X}, {is_free}")
        if last_free == is_free:
            self.markers[-1] = new_end
        else:
            self.markers.append(new_end)

    def __is_free(self, ind):
        return ((ind % 2 == 0) == self.first_free)

    # First fit.  Location must be after hint
    def get_free_addr(self, size, hint=0):
        # block associated with its left marker, so search to len-2
        ind = self.__search(0, len(self.markers)-2, hint)

        # print(f"Searching for {size} free bytes.")
        if self.__is_free(ind) and (self.markers[ind+1]-hint > 0):
            return hint
        else:
            if not self.__is_free(ind):
                ind += 1

            start = ind
            ret = None
            for x in range(start, len(self.markers)-1, 2):
                # print(f"({self.markers[x]}, {self.markers[x+1]})")
                # print(f"Size: {self.markers[x+1]-self.markers[x]}")

                # Almost always you want to avoid a write overlapping two
                # different banks, so there's an additional check beyond
                # just having enough room.
                if self.markers[x+1]-self.markers[x] >= size and \
                   self.markers[x] % 0x10000 + size < 0x10000:

                    # print('Found.')
                    ret = self.markers[x]
                    break

            if ret is None:
                print("Error: Not enough free space.")
                exit()

            return ret

    # Sometimes data needs the same bank, so
    def get_same_bank_free_addrs(self, sizes: list[int],
                                 hint: int = 0) -> list[int]:

        if not sizes:
            return []

        tries = [0 for x in sizes]
        perm = [i for i in range(len(sizes))]

        # going to assign in sorted order.
        # Should discard heavily used blocks more quickly.
        # Save the permutation to recover the original order
        sort_sizes, perm = zip(*sorted(zip(sizes, perm), reverse=True))

        start = hint

        while True:
            tries[0] = self.get_free_addr(sort_sizes[0], start)
            self.mark_block((tries[0], tries[0]+sort_sizes[0]), False)

            first_bank = (tries[0] >> 16) << 16

            success = True

            for i in range(1, len(sort_sizes)):
                tries[i] = self.get_free_addr(sort_sizes[i], first_bank)
                this_bank = (tries[i] >> 16) << 16

                if this_bank != first_bank:
                    success = False
                    start = this_bank

                    # undo previous markings
                    for j in range(0, i):
                        self.mark_block((tries[j], tries[j]+sort_sizes[j]),
                                        True)
                else:
                    # Mark and proceed to next
                    self.mark_block((tries[i], tries[i]+sort_sizes[i]), False)

            if success:
                break

        # Undo markings.  This is sort of ugly.  It would be nice to separate
        # the buffer from the freespace checker so that we can copy the
        # freespace checker and mess with that while finding addresses.
        for i in range(len(tries)):
            self.mark_block((tries[i], tries[i]+sort_sizes[i]), True)

        perm, tries = zip(*sorted(zip(perm, tries)))

        return list(tries)

    '''
    # writes data into the buffer.  The write can introduce free space, such
    # as when ipswriter extends a rom.  So the is_free flag (default False)
    # indicates whether the written area is free or not.
    def write_data(self, addr, data, is_free=False):

        x = self.tell()

        self.seek(addr)
        self.write(data, is_free)

        self.seek(x)
    '''

    # Mark a file with Anskiy's .txt patch format
    # Duplicates much code.  Consider adding patching functionality into
    # this file.
    def mark_blocks_txt_obj(self, patch_obj):
        p = patch_obj

        for line in p:
            line = line.split(":")
            address = int(line[0], 0x10)
            length = int(line[1], 0x10)
            bytes = line[2]
            bytes = bytes.split(" ")

            self.mark_block((address, address+length), False)
            """
            while i < length:
                bytes[i] = int(bytes[i],0x10)
                f.seek(address)
                f.write(st.pack("B",bytes[i]))
                address += 1
                i += 1
            """

    def mark_blocks_txt(self, patch_filename):
        with open(patch_filename, 'r') as patch_obj:
            self.mark_blocks_txt_obj(patch_obj)

    # dupicates much code from ipswriter...
    def mark_blocks_ips_obj(self, ips_obj):
        p = ips_obj

        p.seek(0, 2)
        patch_size = p.tell()

        p.seek(5)  # ignore the "PATCH" at the start

        while p.tell() < patch_size - 5:

            # Get the location of the payload
            addr_bytes = p.read(3)
            addr = get_value_from_bytes_be(addr_bytes)

            # Get the size of the payload
            size_bytes = p.read(2)
            size = get_value_from_bytes_be(size_bytes)

            mark = True
            if size == 0:
                # RLE block
                rle_size_bytes = p.read(2)
                rle_size = get_value_from_bytes_be(rle_size_bytes)

                rle_byte = p.read(1)

                # This can probably be more precise.  For now just note that
                # large repeat 0 blocks are not used space.  This is especially
                # true at the end of the rom.
                if rle_byte[0] == 0 and rle_size >= 0x10:
                    mark = False

                payload = bytearray([rle_byte[0]]*rle_size)
            else:
                # Normal block
                payload = p.read(size)

            # Don't actually write!  Just mark!
            # f.seek(addr)
            # f.write(payload)
            if mark:
                self.mark_block((addr, addr+len(payload)), False)

    def mark_blocks_ips(self, filename):
        with open(filename, 'rb') as ips_obj:
            self.mark_blocks_ips_obj(ips_obj)

    def print_blocks(self):

        print('Free blocks: ')

        if self.first_free is True:
            start = 0
        else:
            start = 1

        for x in range(start, len(self.markers)-1, 2):
            print('[%6.6X, %6.6X)\t %X bytes'
                  % (self.markers[x], self.markers[x+1],
                     (self.markers[x+1]-self.markers[x])))

        print('Used blocks: ')

        if self.first_free is True:
            start = 1
        else:
            start = 0

        for x in range(start, len(self.markers)-1, 2):
            print('[%6.6X, %6.6X)\t %X bytes'
                  % (self.markers[x], self.markers[x+1],
                     (self.markers[x+1]-self.markers[x])))

    # Find the index of an address in the block map
    def __search(self, start_ind, end_ind, addr):
        search_ind = (start_ind+end_ind)//2

        left = self.markers[search_ind]
        right = self.markers[search_ind+1]

        if left <= addr < right:
            return search_ind
        elif addr >= right:
            if start_ind == len(self.markers)-1:
                return len(self.markers)-2
            else:
                return self.__search(search_ind+1, end_ind, addr)
        else:
            return self.__search(start_ind, search_ind-1, addr)


class FSRom(BytesIO):

    def __init__(self, rom: bytes, is_free=False):
        super().__init__(rom)
        self.space_manager = FreeSpace(len(rom), is_free)

    # Apply one of Anskiy's .txt patches and mark free space
    # Code copied from patcher.py with few modifications.
    # I am assuming that all writes are using up free space.
    def patch_txt_file(self, filename):
        with open(filename, 'r') as patch_obj:
            self.patch_txt(patch_obj)

    def patch_txt(self, patch_obj):
        for line in patch_obj:
            line = line.split(":")
            address = int(line[0], 0x10)
            data = bytearray.fromhex(line[2])

            # print(f"{address:06X}: ")
            # print(' '.join(f"{x:02X}" for x in data))
            self.seek(address)
            self.write(data, FSWriteType.MARK_USED)

    # Apply an ips patch.  Most writes are considered used space, but long
    # rle blocks of 0s are considered free space.
    def patch_ips_file(self, filename):
        with open(filename, 'rb') as patch_obj:
            self.patch_ips(patch_obj)

    def patch_ips(self, patch_obj):
        p = patch_obj

        p.seek(0, 2)
        patch_size = p.tell()

        p.seek(5)  # ignore the "PATCH" at the start

        while p.tell() < patch_size - 5:

            # Get the location of the payload
            addr_bytes = p.read(3)
            addr = get_value_from_bytes_be(addr_bytes)

            # Get the size of the payload
            size_bytes = p.read(2)
            size = get_value_from_bytes_be(size_bytes)

            mark_set = FSWriteType.MARK_USED

            if size == 0:
                # RLE block
                rle_size_bytes = p.read(2)
                rle_size = get_value_from_bytes_be(rle_size_bytes)

                rle_byte = p.read(1)

                # Runs of a single symbol are usually free space?
                # IPS will write 0 blocks to extend the length of a file.
                # We should mark these as free
                if rle_byte[0] == 0 and rle_size >= 0x10:
                    mark_set = FSWriteType.MARK_FREE

                payload = bytearray([rle_byte[0]]*rle_size)
            else:
                # Normal block
                payload = p.read(size)

            self.seek(addr)
            self.write(payload, mark_set)

    def write(self, payload,
              write_mark: FSWriteType = FSWriteType.NO_MARK):
        # avoid long names
        spaceman = self.space_manager

        start = self.tell()
        end = start+len(payload)

        self.seek(0, 2)
        buf_end = self.tell()
        self.seek(start)
        BytesIO.write(self, payload)

        if end > buf_end:
            if write_mark == FSWriteType.NO_MARK:
                print('Error: Write extended buffer with NO_MARK set')
                exit()
            else:
                spaceman.extend_end_marker(end, write_mark)

        spaceman.mark_block((start, end), write_mark)

    # writes data to the buffer and marks the space as no longer free.
    # Errors out if there is insufficient space
    # returns the address where the data gets written
    def write_data_to_freespace(self, data, hint=0):
        spaceman = self.space_manager
        write_addr = spaceman.get_free_addr(self, len(data), hint)

        if write_addr is None and hint != 0:
            print('Warning: Insufficient free space.  Ignoring hint.')
            write_addr = spaceman.get_free_addr(self, len(data), 0)

        if write_addr is None:
            print('Error: Insufficient free space. Quitting.')
            quit()
        else:
            self.seek(write_addr)
            self.write(write_addr, FSWriteType.MARK_USED)
            return write_addr


def main():

    fs = FreeSpace(0x600000, True)
    fs.mark_block((0, 0x400000), FSWriteType.MARK_USED)

    fs.mark_blocks_ips('./patch.ips')
    fs.mark_blocks_txt('./patches/patch_codebase.txt')
    fs.print_blocks()

    with open('./roms/ct.sfc', 'rb') as infile:
        fsrom = FSRom(infile.read(), False)

    fsrom.patch_ips_file('./patch.ips')
    fsrom.patch_txt_file('./patches/patch_codebase.txt')
    fsrom.print_blocks()


# Test using patch.ips and patch_codebase.txt
if __name__ == '__main__':
    main()
