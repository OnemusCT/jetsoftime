import unittest
from PyQt6.QtCore import QModelIndex, Qt
from editorui.commanditem import CommandItem
from editorui.commanditemmodel import CommandModel, print_command_tree
from eventcommand import EventCommand, event_commands, FuncSync

class TestCommandModel(unittest.TestCase):
    def setUp(self):
        # Create a root item with some test commands
        self.root = CommandItem("Root")
        self.model = CommandModel(self.root)

    # Append a command and return the next address
    def append_command(self, command: EventCommand, address: int) -> tuple[int, CommandItem]:
        i = self.model.rowCount(QModelIndex())
        self.model.insert_command(QModelIndex(), i, command, address)
        inserted = self.model.index(i, 0, QModelIndex()).internalPointer()
        self.assertEqual(inserted.address, address)
        self.assertEqual(inserted.command, command)
        return (address + len(command), inserted)


    def test_basic_insertion(self):
        """Test basic command insertion functionality"""
        # Create a call PC function command
        command = EventCommand.call_pc_function(0, 1, 2, FuncSync.HALT)
        
        # Insert at root level
        success = self.model.insert_command(QModelIndex(), 0, command, 0x100)
        
        # Verify insertion
        self.assertTrue(success)
        self.assertEqual(self.model.rowCount(QModelIndex()), 1)
        
        # Verify command properties
        index = self.model.index(0, 0, QModelIndex())
        item = index.internalPointer()
        self.assertEqual(item.address, 0x100)
        self.assertEqual(item.command, command)

    def test_nested_insertion(self):
        """Test insertion of commands under conditional commands"""
        # Create an IF command (conditional)
        if_command = EventCommand.if_has_item(1, 8)  # Jump 8 bytes if item 1 not present
        
        # Insert conditional command
        self.model.insert_command(QModelIndex(), 0, if_command, 0x100)
        parent_index = self.model.index(0, 0, QModelIndex())
        
        # Insert a return command under conditional
        child_command = EventCommand.return_cmd()
        success = self.model.insert_command(parent_index, 0, child_command, 0x104)
        
        # Verify nested structure
        self.assertTrue(success)
        self.assertEqual(self.model.rowCount(parent_index), 1)
        
        # Verify addresses are correct
        child_index = self.model.index(0, 0, parent_index)
        child_item = child_index.internalPointer()
        self.assertEqual(child_item.address, 0x104)

    def test_command_deletion(self):
        """Test command deletion and address updating"""
        # Insert two commands
        cmd1 = EventCommand.script_speed(1)  # Single byte command
        cmd2 = EventCommand.set_speed(2)     # Another single byte command
        
        self.model.insert_command(QModelIndex(), 0, cmd1, 0x100)
        self.model.insert_command(QModelIndex(), 1, cmd2, 0x102)
        
        # Delete first command
        index_to_delete = self.model.index(0, 0, QModelIndex())
        success = self.model.delete_command(index_to_delete)
        
        # Verify deletion
        self.assertTrue(success)
        self.assertEqual(self.model.rowCount(QModelIndex()), 1)
        
        # Verify address of remaining command was updated
        remaining_index = self.model.index(0, 0, QModelIndex())
        remaining_item = remaining_index.internalPointer()
        self.assertEqual(remaining_item.command.command, cmd2.command)
        self.assertEqual(remaining_item.address, 0x100)  # Should have moved up

    def test_forward_jump_command_updates(self):
        """Test that jump commands are properly updated when commands are inserted/deleted/updated"""
        # Create a forward jump command (jump 8 bytes forward)
        jump_cmd = EventCommand.jump_forward(8)
        self.model.insert_command(QModelIndex(), 0, jump_cmd, 0x100)
        
        # Insert a pause command after the jump but before its target
        new_cmd = EventCommand.pause(1)  # 1 second pause
        self.model.insert_command(QModelIndex(), 1, new_cmd, 0x102)
        
        # Verify jump offset was updated
        jump_index = self.model.index(0, 0, QModelIndex())
        jump_item = jump_index.internalPointer()
        self.assertEqual(jump_item.command.args[0], 8+len(new_cmd))  # Jump should be increased

        to_change = self.model.index(1,0,QModelIndex()).internalPointer()
        end_cmd = EventCommand.end_cmd()
        self.model.update_command(to_change, end_cmd)
        jump_item = jump_index.internalPointer()
        self.assertEqual(jump_item.command.args[0], 8+len(end_cmd)) # Should reflect the updated value
    
        self.model.delete_command(self.model.index(1,0, QModelIndex()))
        jump_item = jump_index.internalPointer()
        self.assertEqual(jump_item.command.args[0], 8) # Back to the original value

    def test_back_jump_command_updates(self):
        """Test that jump commands are properly updated when commands are inserted/deleted/updated"""
        base_address = 0x100
        current_address = base_address
        # Insert a pause command that the back jump will point to
        current_address, pause_cmd = self.append_command(EventCommand.pause(1), current_address)
        # Add a jump to the pause
        first_bytes_to_jump = current_address-base_address + 1
        first_jump_cmd_index = self.model.rowCount(QModelIndex())
        first_jump_address = current_address
        current_address, first_jump_cmd = self.append_command(EventCommand.jump_back(first_bytes_to_jump), current_address)
        
        # Add some additional commands and a back jump that isn't directly affected
        current_address, end1 = self.append_command(EventCommand.end_cmd(), current_address)
        current_address, end2 = self.append_command(EventCommand.end_cmd(), current_address)

        second_bytes_to_jump = current_address-end2.address + 1
        second_jump_cmd_index = self.model.rowCount(QModelIndex())
        second_jump_address = current_address
        current_address, second_jump_cmd = self.append_command(EventCommand.jump_back(second_bytes_to_jump), current_address)

        print_command_tree(self.model)
        # The setup is complete, now insert a command prior to the first jump.
        inserted_cmd = EventCommand.end_cmd()
        inserted_len = len(inserted_cmd)
        self.model.insert_command(QModelIndex(), 1, inserted_cmd, pause_cmd.address)

        # An additional command was inserted before both jumps
        first_jump_cmd_index+=1
        second_jump_cmd_index+=1

        # Verify that the command matches, the arg has been updated, and the address has shifted.
        new_j1 = self.model.index(first_jump_cmd_index, 0, QModelIndex()).internalPointer()
        self.assertEqual(new_j1.command.command, first_jump_cmd.command.command)
        self.assertEqual(new_j1.command.args[0], first_bytes_to_jump+inserted_len)
        self.assertEqual(new_j1.address, first_jump_address + inserted_len)

        # Verify that the command matches, the arg has NOT been updated, and the address has shifted.
        new_j2 = self.model.index(second_jump_cmd_index, 0, QModelIndex()).internalPointer()
        self.assertEqual(new_j2.command.command, second_jump_cmd.command.command)
        self.assertEqual(new_j2.command.args[0], second_bytes_to_jump)
        self.assertEqual(new_j2.address, second_jump_address + inserted_len)
    
        updated_cmd = EventCommand.add_gold(1)
        updated_cmd_length = len(updated_cmd)
        self.model.update_command(self.model.index(1,0,QModelIndex()).internalPointer(), updated_cmd)

        # Validate that the address and args have changed
        new_j1 = self.model.index(first_jump_cmd_index, 0, QModelIndex()).internalPointer()
        self.assertEqual(new_j1.command.command, first_jump_cmd.command.command)
        self.assertEqual(new_j1.command.args[0], first_bytes_to_jump+updated_cmd_length)
        self.assertEqual(new_j1.address, first_jump_address + updated_cmd_length)

        # Validate that only the address has changed
        new_j2 = self.model.index(second_jump_cmd_index, 0, QModelIndex()).internalPointer()
        self.assertEqual(new_j2.command.command, second_jump_cmd.command.command)
        self.assertEqual(new_j2.command.args[0], second_bytes_to_jump)
        self.assertEqual(new_j2.address, second_jump_address + updated_cmd_length)

        # Now delete the inserted item and verify that things have returned to their
        # original state
        self.model.delete_command(self.model.index(1,0,QModelIndex()))
        first_jump_cmd_index -= 1
        second_jump_cmd_index -= 1

        new_j1 = self.model.index(first_jump_cmd_index, 0, QModelIndex()).internalPointer()
        self.assertEqual(new_j1.command.command, first_jump_cmd.command.command)
        self.assertEqual(new_j1.command.args[0], first_bytes_to_jump)
        self.assertEqual(new_j1.address, first_jump_address)

        # Validate that only the address has changed
        new_j2 = self.model.index(second_jump_cmd_index, 0, QModelIndex()).internalPointer()
        self.assertEqual(new_j2.command.command, second_jump_cmd.command.command)
        self.assertEqual(new_j2.command.args[0], second_bytes_to_jump)
        self.assertEqual(new_j2.address, second_jump_address)


    def test_drag_drop(self):
        """Test drag and drop functionality"""
        # Insert two commands
        cmd1 = EventCommand.script_speed(1)
        cmd2 = EventCommand.set_speed(2)
        
        self.model.insert_command(QModelIndex(), 0, cmd1, 0x100)
        self.model.insert_command(QModelIndex(), 1, cmd2, 0x102)
        
        # Create mime data for drag operation
        indexes = [self.model.index(0, 0, QModelIndex())]
        mime_data = self.model.mimeData(indexes)
        
        # Verify drop is allowed
        self.assertTrue(self.model.canDropMimeData(
            mime_data, 
            Qt.DropAction.MoveAction,
            1, 0, 
            self.model.index(1, 0, QModelIndex())
        ))
        
        # Perform drop
        success = self.model.dropMimeData(
            mime_data,
            Qt.DropAction.MoveAction,
            1, 0,
            self.model.index(1, 0, QModelIndex())
        )
        
        self.assertTrue(success)
        # Verify order of items after drop
        first_item = self.model.index(0, 0, QModelIndex()).internalPointer()
        self.assertEqual(first_item.command, cmd2)

    def test_multi_byte_command_addressing(self):
        """Test address handling with variable-length commands"""
        # Create a complex command that takes multiple bytes
        battle_cmd = EventCommand.battle(no_win_pose=True, bottom_menu=True)
        self.model.insert_command(QModelIndex(), 0, battle_cmd, 0x100)
        
        # Add a simple command after it
        pause_cmd = EventCommand.pause(1)
        self.model.insert_command(QModelIndex(), 1, pause_cmd, 0x103)  # Should be 3 bytes later
        
        # Verify correct address calculation
        pause_index = self.model.index(1, 0, QModelIndex())
        pause_item = pause_index.internalPointer()
        self.assertEqual(pause_item.address, 0x103)

if __name__ == '__main__':
    unittest.main()