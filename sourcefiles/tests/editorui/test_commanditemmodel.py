import unittest
from PyQt6.QtCore import QModelIndex, Qt
from editorui.commanditem import CommandItem
from editorui.commanditemmodel import CommandModel
from eventcommand import EventCommand, event_commands, FuncSync

def print_command_tree(model: CommandModel, output_file=None):
    """
    Print a readable representation of all commands in the model.
    
    Args:
        model: The CommandModel to print
        output_file: Optional file path to write the output. If None, prints to console.
    """
    def _format_command(item: CommandItem) -> str:
        """Format a single command item into a readable string"""
        if not item.command:
            return f"{item.name}"
            
        # Get command details
        cmd_id = item.command.command
        args = [f"0x{arg:X}" if isinstance(arg, int) else str(arg) 
               for arg in item.command.args]
        args_str = ", ".join(args)
        
        return f"0x{cmd_id:02X} {item.name} @ {item.address} [{args_str}]"

    def _print_recursive(index: QModelIndex, depth: int, output_lines: list):
        """Recursively print command items with proper indentation"""
        if not index.isValid():
            # Handle root level items
            for row in range(model.rowCount(QModelIndex())):
                child_index = model.index(row, 0, QModelIndex())
                _print_recursive(child_index, depth, output_lines)
            return

        # Get item at this index
        item = index.internalPointer()
        indent = "  " * depth
        line = indent + _format_command(item)
        output_lines.append(line)
        
        # Process children
        for row in range(model.rowCount(index)):
            child_index = model.index(row, 0, index)
            _print_recursive(child_index, depth + 1, output_lines)

    # Generate all lines
    output_lines = []
    _print_recursive(QModelIndex(), 0, output_lines)
    
    # Write output
    if output_file:
        with open(output_file, 'w') as f:
            for line in output_lines:
                f.write(line + '\n')
    else:
        for line in output_lines:
            print(line)
        print("\n\n")

class TestCommandModel(unittest.TestCase):
    def setUp(self):
        # Create a root item with some test commands
        self.root = CommandItem("Root")
        self.model = CommandModel(self.root)

    def test_basic_insertion(self):
        """Test basic command insertion functionality"""
        # Create a call PC function command
        command = EventCommand.call_pc_function(0, 1, 2, FuncSync.HALT)
        
        # Insert at root level
        success = self.model.insert_command(QModelIndex(), 0, command, "0x100")
        
        # Verify insertion
        self.assertTrue(success)
        self.assertEqual(self.model.rowCount(QModelIndex()), 1)
        
        # Verify command properties
        index = self.model.index(0, 0, QModelIndex())
        item = index.internalPointer()
        self.assertEqual(item.address, "0x100")
        self.assertEqual(item.command, command)

    def test_nested_insertion(self):
        """Test insertion of commands under conditional commands"""
        # Create an IF command (conditional)
        if_command = EventCommand.if_has_item(1, 8)  # Jump 8 bytes if item 1 not present
        
        # Insert conditional command
        self.model.insert_command(QModelIndex(), 0, if_command, "0x100")
        parent_index = self.model.index(0, 0, QModelIndex())
        
        # Insert a return command under conditional
        child_command = EventCommand.return_cmd()
        success = self.model.insert_command(parent_index, 0, child_command, "0x104")
        
        # Verify nested structure
        self.assertTrue(success)
        self.assertEqual(self.model.rowCount(parent_index), 1)
        
        # Verify addresses are correct
        child_index = self.model.index(0, 0, parent_index)
        child_item = child_index.internalPointer()
        self.assertEqual(child_item.address, "0x104")

    def test_command_deletion(self):
        """Test command deletion and address updating"""
        # Insert two commands
        cmd1 = EventCommand.script_speed(1)  # Single byte command
        cmd2 = EventCommand.set_speed(2)     # Another single byte command
        
        self.model.insert_command(QModelIndex(), 0, cmd1, "0x100")
        self.model.insert_command(QModelIndex(), 1, cmd2, "0x102")
        
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
        self.assertEqual(remaining_item.address, "0x100")  # Should have moved up

    # def test_conditional_command_promotion(self):
    #     """Test that children of conditional commands are properly promoted when parent is deleted"""
    #     # Create IF command with children (if_has_item takes 2 bytes)
    #     if_command = EventCommand.if_has_item(1, 8)  
    #     self.model.insert_command(QModelIndex(), 0, if_command, "0x100")
    #     parent_index = self.model.index(0, 0, QModelIndex())
        
    #     # Add two child commands (each takes 2 bytes)
    #     child1 = EventCommand.script_speed(1)
    #     child2 = EventCommand.set_speed(2)
    #     self.model.insert_command(parent_index, 0, child1, "0x103")  # After IF command bytes
    #     self.model.insert_command(parent_index, 1, child2, "0x105")  
        
    #     # Get initial addresses for verification
    #     first_child_before = self.model.index(0, 0, parent_index).internalPointer()
    #     second_child_before = self.model.index(1, 0, parent_index).internalPointer()
    #     self.assertEqual(first_child_before.address, "0x103")
    #     self.assertEqual(second_child_before.address, "0x105")
        
    #     # Delete conditional command
    #     success = self.model.delete_command(parent_index)
        
    #     # Verify children were promoted to root level
    #     self.assertTrue(success)
    #     self.assertEqual(self.model.rowCount(QModelIndex()), 2)
        
    #     # After promotion, addresses should be adjusted by size of parent IF command (2 bytes)
    #     first_child = self.model.index(0, 0, QModelIndex()).internalPointer()
    #     second_child = self.model.index(1, 0, QModelIndex()).internalPointer()
    #     self.assertEqual(first_child.address, "0x101")
    #     self.assertEqual(second_child.address, "0x103")

    def test_forward_jump_command_updates(self):
        """Test that jump commands are properly updated when commands are inserted/deleted/updated"""
        # Create a forward jump command (jump 8 bytes forward)
        jump_cmd = EventCommand.jump_forward(8)
        self.model.insert_command(QModelIndex(), 0, jump_cmd, "0x100")
        
        # Insert a pause command after the jump but before its target
        new_cmd = EventCommand.pause(1)  # 1 second pause
        self.model.insert_command(QModelIndex(), 1, new_cmd, "0x102")
        
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
        # Insert a pause command that the back jump will point to
        base_address = 0x100
        new_cmd = EventCommand.pause(1)  # 1 second pause
        self.model.insert_command(QModelIndex(), 0, new_cmd, "0x{:02X}".format(base_address))
        
        second_address = base_address + len(new_cmd)
        jump_cmd = EventCommand.jump_back(len(new_cmd) + 1)
        self.model.insert_command(QModelIndex(), 1, jump_cmd, "0x{:02X}".format(second_address))
        self.assertEqual(self.model.index(1, 0, QModelIndex()).internalPointer().address, "0x{:02X}".format(second_address))

        inserted_cmd = EventCommand.end_cmd()
        self.model.insert_command(QModelIndex(), 1, inserted_cmd, "0x{:02X}".format(second_address))
        jump_address = second_address + len(inserted_cmd)
        
        # Verify jump offset was updated
        jump_index = self.model.index(2, 0, QModelIndex())
        jump_item = jump_index.internalPointer()
        self.assertEqual(jump_item.command.command, 0x11)
        self.assertEqual(jump_item.address, "0x{:02X}".format(jump_address))
        self.assertEqual(jump_item.command.args[0], 3)

        to_change = self.model.index(1,0,QModelIndex()).internalPointer()
        add_val_to_mem = EventCommand.add_value_to_mem(1,0x7f0200)
        self.model.update_command(to_change, add_val_to_mem)

        jump_index = self.model.index(2, 0, QModelIndex())
        jump_item = jump_index.internalPointer()
        self.assertEqual(jump_item.command.command, 0x11)
        # jump address should have shifted by the diff between an end command
        # and add_val_to_mem. end is a 1 byte command and add_val_to_mem is a
        # 3 byte command
        self.assertEqual(jump_item.address, "0x{:02X}".format(jump_address + 2))
        self.assertEqual(jump_item.command.args[0], 5)

        self.model.delete_command(self.model.index(1,0,QModelIndex()))

        jump_index = self.model.index(1, 0, QModelIndex())
        jump_item = jump_index.internalPointer()
        self.assertEqual(jump_item.command.command, 0x11)
        # jump address should have shifted by the diff between an end command
        # and add_val_to_mem. end is a 1 byte command and add_val_to_mem is a
        # 3 byte command
        self.assertEqual(jump_item.address, "0x{:02X}".format(base_address + 1))
        self.assertEqual(jump_item.command.args[0], 2)

    def test_drag_drop(self):
        """Test drag and drop functionality"""
        # Insert two commands
        cmd1 = EventCommand.script_speed(1)
        cmd2 = EventCommand.set_speed(2)
        
        self.model.insert_command(QModelIndex(), 0, cmd1, "0x100")
        self.model.insert_command(QModelIndex(), 1, cmd2, "0x102")
        
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
        self.model.insert_command(QModelIndex(), 0, battle_cmd, "0x100")
        
        # Add a simple command after it
        pause_cmd = EventCommand.pause(1)
        self.model.insert_command(QModelIndex(), 1, pause_cmd, "0x103")  # Should be 3 bytes later
        
        # Verify correct address calculation
        pause_index = self.model.index(1, 0, QModelIndex())
        pause_item = pause_index.internalPointer()
        self.assertEqual(pause_item.address, "0x103")

if __name__ == '__main__':
    unittest.main()