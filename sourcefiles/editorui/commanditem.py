from __future__ import annotations

from eventcommand import EventCommand


class CommandItem:
    def __init__(self, name, command: EventCommand = None, address: int = None, children: list[CommandItem] | None = None):
        self.name = name
        self.command = command
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

    @property
    def row(self) -> int:
        """Get the row number of this item within its parent's children."""
        if self.parent:
            return self.parent.children.index(self)
        return 0