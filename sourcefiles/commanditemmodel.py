from __future__ import annotations
from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt6.QtWidgets import QApplication, QTreeView
from eventcommand import EventCommand
import commandtotext as c2t

class CommandItem:
    def __init__(self, name, command: EventCommand = None, address: str = None, children: list[CommandItem] | None = None):
        self.name = name
        self.command = command
        print(self.command)
        self.address = address
        self.children = children if children is not None else []
        self.parent = None
    
    def add_child(self, child: CommandItem):
        child.parent = self
        self.children.append(child)
    
    def get_child(self, index: int) -> CommandItem:
        if index < len(self.children):
            return self.children[index]
        return None
    
    def add_children(self, children: list[CommandItem]):
        for c in children:
            c.parent = self
            self.children.append(c)

class CommandModel(QAbstractItemModel):
    def __init__(self, root_item: CommandItem, parent=None):
        super().__init__(parent)
        self._root_item = root_item

    def get_all_items_after(self, start_item: CommandItem) -> list[CommandItem]:
        """Get all items that come after the given item in a depth-first traversal"""
        items = []
        
        def collect_items(item: CommandItem, collecting: bool):
            # If we're collecting or this is the start item, start collecting its siblings
            if collecting or item == start_item:
                collecting = True
            
            # If we're collecting, add all subsequent siblings
            if collecting:
                next_sibling_idx = item.parent.children.index(item) + 1
                siblings = item.parent.children[next_sibling_idx:]
                for sibling in siblings:
                    items.append(sibling)
                    self._collect_all_children(sibling, items)
            
            # Process children
            for child in item.children:
                collect_items(child, collecting)
        
        # Start from root if the item's parent is None
        if start_item.parent is None:
            root_children = self._root_item.children
            start_idx = root_children.index(start_item)
            items.extend(root_children[start_idx + 1:])
            for item in root_children[start_idx + 1:]:
                self._collect_all_children(item, items)
        else:
            collect_items(self._root_item, False)
        
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
        # Calculate size difference
        old_size = len(item.command) if item.command else 0
        new_size = len(new_command)
        size_diff = new_size - old_size
        
        # Get the model index for this item
        item_index = self.get_index_for_item(item)
        print(item_index.internalPointer().command)
        
        # Update the command
        item.command = new_command
        item.name = c2t.command_to_text(item.command, int(item.address,16))
        # Emit signal for possible command-related display changes
        self.dataChanged.emit(
            self.createIndex(item_index.row(), 0, item),
            self.createIndex(item_index.row(), 1, item),
            [Qt.ItemDataRole.DisplayRole]
        )
        
        if size_diff != 0:  # Only update addresses if size changed
            # Get all items that come after this one
            affected_items = self.get_all_items_after(item)
            
            # Update their addresses
            for affected_item in affected_items:
                if affected_item.address:
                    old_addr = int(affected_item.address, 16)
                    new_addr = old_addr + size_diff
                    affected_item.address = f"0x{new_addr:X}"
                    
                    # Get index for affected item and emit change signal
                    affected_index = self.get_index_for_item(affected_item)
                    self.dataChanged.emit(
                        self.createIndex(affected_index.row(), 1, affected_item),
                        self.createIndex(affected_index.row(), 1, affected_item),
                        [Qt.ItemDataRole.DisplayRole]
                    )


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
                return item.address if item.address is not None else ""
        
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return ["Name", "Address"][section]
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
        
        # Replace the root item
        self._root_item = new_root_item
        
        # Tell views we're done
        self.endResetModel()