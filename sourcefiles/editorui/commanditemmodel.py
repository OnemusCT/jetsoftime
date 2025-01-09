from __future__ import annotations
from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt, QMimeData
from eventcommand import EventCommand
import editorui.commandtotext as c2t
from editorui.commanditem import CommandItem

class CommandModel(QAbstractItemModel):
    def __init__(self, root_item: CommandItem, parent=None):
        super().__init__(parent)
        self._root_item = root_item

    def _update_addresses(self,  modified_item: CommandItem, size_change: int, insertion: bool = False):
        all_commands = _get_all_commands(self._root_item)
        # print("Modified address: 0x{:02X}".format(modified_item.address))
        seen_modified = False
        for command in all_commands:
            changed = False
            if command.address:
                # print("Checking 0x{:02X} - {}".format(command.address, command.command))
                if command.address > modified_item.address:
                    command.address += size_change
                    changed = True
                # If there is an insertion there are going to be two commands
                # with the same address, the original and the newly inserted.
                # We only want to update the second of the two.
                elif insertion and command.address == modified_item.address:
                    if not seen_modified:
                        seen_modified = True
                    else: 
                        command.address += size_change
                        changed = True
            if command.command and (command.command.command == 0x10 or command.command.command == 0x11):
                command.name = c2t.command_to_text(command.command, command.address, [])
                changed = True
            if changed:
                affected_index = self.get_index_for_item(command)
                self.dataChanged.emit(
                    self.createIndex(affected_index.row(), 0, affected_index.internalPointer()),
                    self.createIndex(affected_index.row(), 1, affected_index.internalPointer()),
                    [Qt.ItemDataRole.DisplayRole]
                )

    def supportedDropActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled
        return default_flags | Qt.ItemFlag.ItemIsDropEnabled

    def mimeTypes(self) -> list[str]:
        return ['application/x-commanditem']

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:
        mime_data = QMimeData()
        encoded_data = bytearray()
        
        # Store the row and parent information for each index
        selected_items = []
        for index in indexes:
            if index.column() == 0:  # Only process first column
                item = index.internalPointer()
                selected_items.append(item)
        
        # Store the selected items in mime data
        mime_data.setData('application/x-commanditem', bytes(str(id(selected_items)), 'utf-8'))
        # Store the actual items in a class variable for access during drop
        self._drag_items = selected_items
        return mime_data

    def canDropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if not data.hasFormat('application/x-commanditem'):
            return False
            
        if not hasattr(self, '_drag_items'):
            return False
            
        # Get target item
        target_item = parent.internalPointer() if parent.isValid() else self._root
        
        # Check if any dragged item is an ancestor of the target
        for item in self._drag_items:
            current = target_item
            while current is not None:
                if current == item:
                    print("Error: Cannot drop an item onto its own descendant")
                    return False
                current = current.parent
                
        return True

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if not self.canDropMimeData(data, action, row, column, parent):
            return False

        if action == Qt.DropAction.IgnoreAction:
            return True

        # Get target item and dragged items
        target_item = parent.internalPointer() if parent.isValid() else self._root_item
        
        # Remove items from their current positions
        items_to_move = []
        for item in self._drag_items:
            if item.parent:
                old_parent = item.parent
                old_row = old_parent.children.index(item)
                self.beginRemoveRows(self.createIndex(0, 0, old_parent), old_row, old_row)
                old_parent.children.remove(item)
                self.endRemoveRows()
                items_to_move.append(item)

        # Determine insert position and parent
        if target_item.children and target_item.command and target_item.command.command in EventCommand.conditional_commands:
            # Case 1: Dropping onto a conditional command - insert at beginning of its children
            target_parent = target_item
            insert_pos = 0
        else:
            # Case 2: Dropping after a command - insert after it in its parent
            target_parent = target_item.parent if target_item.parent else self._root_item
            insert_pos = target_parent.children.index(target_item) + 1

        # Insert items at new position
        self.beginInsertRows(self.get_index_for_item(target_parent), 
                           insert_pos, 
                           insert_pos + len(items_to_move) - 1)
        
        for item in items_to_move:
            item.parent = target_parent
            target_parent.children.insert(insert_pos, item)
            insert_pos += 1
            
        self.endInsertRows()
        return True

    def get_all_items_after(self, start_item: CommandItem) -> list[CommandItem]:
        """Get all items that come after the given item in a depth-first traversal of the entire tree"""
        items = []
        found_start = False
        
        def traverse(item: CommandItem):
            nonlocal found_start, items
            
            # Check if this is the start item
            if item == start_item:
                found_start = True
                return
                
            # If we've found the start item, add this item to our list
            if found_start:
                items.append(item)
                
            # Continue traversing children
            for child in item.children:
                traverse(child)
        
        def traverse_from_root():
            nonlocal found_start, items  # Add nonlocal declaration here
            
            # Start with root's children
            for root_child in self._root_item.children:
                # If we've found our start item, add all subsequent items
                if found_start:
                    items.append(root_child)
                    # Add all descendants of this item
                    for child in root_child.children:
                        traverse(child)
                else:
                    # If this is our start item, mark it and continue to next sibling
                    if root_child == start_item:
                        found_start = True
                        continue
                        
                    # Haven't found start item yet, traverse this subtree
                    traverse(root_child)
        
        # Start the traversal
        traverse_from_root()
        return items

    def _collect_all_children(self, item: CommandItem, items: list[CommandItem]):
        """Helper method to collect all children of an item"""
        for child in item.children:
            items.append(child)
            self._collect_all_children(child, items)

    def get_index_for_item(self, item: CommandItem) -> QModelIndex:
        """Find the model index for a given item"""
        if item == self._root_item or item is None:
            return QModelIndex()
            
        if item.parent == self._root_item:
            row = self._root_item.children.index(item)
            return self.createIndex(row, 0, item)
        else:
            parent = item.parent
            row = parent.children.index(item)
            parent_index = self.get_index_for_item(parent)
            return self.index(row, 0, parent_index)

    def update_command(self, item: CommandItem, new_command: EventCommand):
        """Update an item's command and adjust subsequent addresses based on command size change"""
        print("Updating")
        # Calculate size difference
        old_size = len(item.command) if item.command else 0
        new_size = len(new_command)
        size_diff = new_size - old_size
        
        # Get the model index for this item
        item_index = self.get_index_for_item(item)
        print(item_index.internalPointer().command)
        
        # Handle promotion of children if changing from conditional to non-conditional command
        if item.command.command in EventCommand.conditional_commands and new_command.command not in EventCommand.conditional_commands:
            parent = item.parent
            children_to_promote = item.children[:]
            
            if not children_to_promote:
                # If no children, just update the command
                pass
            elif parent is not None:
                # Find index of current item in parent's children
                item_idx = parent.children.index(item)
                
                # Calculate the insert position (right after the current item)
                insert_position = item_idx + 1
                
                # Notify model about upcoming insertion
                parent_index = self.get_index_for_item(parent)
                self.beginInsertRows(parent_index, insert_position, 
                                insert_position + len(children_to_promote) - 1)
                
                # Update parent references and insert children
                for child in children_to_promote:
                    child.parent = parent
                parent.children[insert_position:insert_position] = children_to_promote
                
                # Clear original children list
                item.children = []
                
                self.endInsertRows()
                
            else:
                # Handle root level promotion
                item_idx = self._root_item.children.index(item)
                insert_position = item_idx + 1
                
                # Notify model about upcoming insertion at root level
                self.beginInsertRows(QModelIndex(), insert_position, 
                                insert_position + len(children_to_promote) - 1)
                
                # Update parent references and insert children
                for child in children_to_promote:
                    child.parent = self._root_item
                self._root_item.children[insert_position:insert_position] = children_to_promote
                
                # Clear original children list
                item.children = []
                
                self.endInsertRows()
        
        # Update the command and name
        item.command = new_command
        item.name = c2t.command_to_text(item.command, item.address, [])
        
        # Emit signal for possible command-related display changes
        self.dataChanged.emit(
            self.createIndex(item_index.row(), 0, item),
            self.createIndex(item_index.row(), 1, item),
            [Qt.ItemDataRole.DisplayRole]
        )
        
        if size_diff != 0:  # Only update addresses if size changed
            # Get all items that come after this one
            self._update_jump_parameters(item, size_diff)
            self._update_addresses(item, size_diff)
            
    def insert_command(self, parent_index: QModelIndex, position: int, command: EventCommand, address: int) -> bool:
        """
        Insert a new command at the specified position.
        
        Args:
            parent_index: Parent model index where command should be inserted
            position: Position in parent's children where command should be inserted
            command: The EventCommand to insert
            address: The hex address where the command will be inserted
            
        Returns:
            bool: True if insertion was successful
        """
        parent_item = self._root_item if not parent_index.isValid() else parent_index.internalPointer()
        
        # Create new command item
        new_item = CommandItem(
            c2t.command_to_text(command, address, []),
            command,
            address
        )
        
        # Notify model about upcoming insertion
        self.beginInsertRows(parent_index, position, position)
        
        # Insert the new item
        new_item.parent = parent_item
        parent_item.children.insert(position, new_item)
        
        # Update addresses of all subsequent commands
        command_size = len(command)
        self._update_jump_parameters(new_item, command_size, True)
        self._update_addresses(new_item, command_size, True)
        
        # End insertion process
        self.endInsertRows()
        return True

    def delete_command(self, index: QModelIndex) -> bool:
        """
        Delete the command at the specified index.
        
        Args:
            index: Model index of command to delete
            
        Returns:
            bool: True if deletion was successful
        """
        if not index.isValid():
            return False
            
        item = index.internalPointer()
        parent_item = item.parent
        if parent_item is None:
            return False
            
        # Get size of command being deleted for address adjustment
        command_size = len(item.command) if item.command else 0
        
        # Get items that will need address updates before deleting
        
        # Get parent index for beginRemoveRows
        parent_index = self.parent(index)
        affected_items = self.get_all_items_after(item)
        
        # Handle children of deleted item if it's a conditional command
        if item.command.command in EventCommand.conditional_commands and item.children:
            # Find position to promote children to
            item_pos = parent_item.children.index(item)
            
            # Remove the item itself
            self.beginRemoveRows(parent_index, index.row(), index.row())
            parent_item.children.pop(index.row())
            self.endRemoveRows()
            
            # Insert promoted children
            self.beginInsertRows(parent_index, item_pos, item_pos + len(item.children) - 1)
            for child in item.children:
                child.parent = parent_item
            parent_item.children[item_pos:item_pos] = item.children
            self.endInsertRows()
        else:
            # Simple removal without child promotion
            self.beginRemoveRows(parent_index, index.row(), index.row())
            parent_item.children.pop(index.row())
            self.endRemoveRows()
        
        item = index.internalPointer()
        self._update_jump_parameters(item, -command_size)
        self._update_addresses(item, -command_size)
        return True

    def rowCount(self, parent: QModelIndex) -> int:
        if not parent.isValid():
            # Root level - return number of root item's children
            return len(self._root_item.children)
        
        # Get the parent item and return its child count
        parent_item: CommandItem = parent.internalPointer()
        return len(parent_item.children)

    def columnCount(self, parent: QModelIndex) -> int:
        return 2  # Two columns: name and address

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        if not index.isValid():
            return None

        item: CommandItem = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 1:
                return item.name
            elif index.column() == 0:
                return "0x{:02X}".format(item.address) if item.address is not None else ""
        
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return ["Address", "Command"][section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            # Getting a top-level item
            parent_item = self._root_item
        else:
            # Getting a child item
            parent_item = parent.internalPointer()

        child_item = parent_item.get_child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item: CommandItem = index.internalPointer()
        parent_item = child_item.parent

        if parent_item is None or parent_item == self._root_item:
            return QModelIndex()

        # Find the row of the parent within its parent's children
        if parent_item.parent is not None:
            row = parent_item.parent.children.index(parent_item)
        else:
            row = 0

        return self.createIndex(row, 0, parent_item)

    def replace_items(self, new_root_item: CommandItem):
        # Tell views we're about to replace everything
        self.beginResetModel()
        
        # Ensure all items have proper parent references
        def setup_parents(item: CommandItem, parent: CommandItem):
            item.parent = parent
            for child in item.children:
                setup_parents(child, item)
        
        # Setup parent references for all items
        for child in new_root_item.children:
            setup_parents(child, new_root_item)
        
        # Replace the root item
        self._root_item = new_root_item
        
        # Tell views we're done
        self.endResetModel()

    def _update_jump_parameters(self, modified_item: CommandItem, size_change: int, insertion=False):
        all_commands = _get_all_commands(self._root_item)
        seen_modified = False
        for item in all_commands:
            if item.command and item.command.command in EventCommand.fwd_jump_commands:
                jump_target = item.address + item.command.args[-1]
                if item.command.command != 0x10:
                    jump_target += len(item.command)
                #print("FWD - Modified addr: {:02X}\nJump Start: {:02X}\nJump Target: {:02X}".format(modified_item.address, jump_start, jump_target))
                # If jump crosses over our modified command, adjust it
                if item.address < modified_item.address and jump_target > modified_item.address:
                    item.command.args[-1] += size_change
                    
                    # Notify model of change
                    item_index = self.get_index_for_item(item)
                    self.dataChanged.emit(
                        self.createIndex(item_index.row(), 0, item),
                        self.createIndex(item_index.row(), 1, item),
                        [Qt.ItemDataRole.DisplayRole]
                    )
            elif item.command and item.command.command == 0x11:
                jump_target = item.address - item.command.args[0]
                address_check = item.address > modified_item.address and jump_target < modified_item.address
                # If this is an insertion there will be two items with the same address. The 
                # inserted item and the item that it was inserted before. We only want
                # to update the address for the item that was already there so we check
                # to see if this is the second time we've seen the "modified" address.
                if insertion and seen_modified:
                    address_check = item.address >= modified_item.address and jump_target < modified_item.address
                # If jump crosses over our modified command, adjust it
                if address_check:
                    item.command.args[0] += size_change
                    
                    # Notify model of change
                    item_index = self.get_index_for_item(item)
                    self.dataChanged.emit(
                        self.createIndex(item_index.row(), 0, item),
                        self.createIndex(item_index.row(), 1, item),
                        [Qt.ItemDataRole.DisplayRole]
                    )
            if item.address == modified_item.address:
                seen_modified = True

def print_command_tree(model: CommandModel):
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
        
        return f"0x{cmd_id:02X} {item.name} @ 0x{item.address:02X} [{args_str}]"

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
    for line in output_lines:
        print(line)
    print("\n")

def _get_all_commands(root: CommandItem) -> list[CommandItem]:
    """Get all commands in the tree in depth-first order"""
    commands = []
    def traverse(item: CommandItem):
        commands.append(item)
        for child in item.children:
            traverse(child)
    traverse(root)
    return commands