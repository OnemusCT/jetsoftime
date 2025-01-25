from editorui.menus.BaseCommandMenu import BaseCommandMenu
from editorui.menus.ValidatingLineEdit import ValidatingLineEdit
from editorui.menus.CommandError import CommandError
from eventcommand import EventCommand, Operation

from PyQt6.QtWidgets import (QComboBox, QLabel, QVBoxLayout, QWidget, 
                           QRadioButton, QButtonGroup, QHBoxLayout)

class CheckDrawnMenu(BaseCommandMenu):
    """Menu for checking if an object is visible"""
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        obj_label = QLabel("Object ID:")
        self.obj_id = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        jump_label = QLabel("Jump bytes if not visible:")
        self.jump_bytes = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        layout.addWidget(obj_label)
        layout.addWidget(self.obj_id)
        layout.addWidget(jump_label)
        layout.addWidget(self.jump_bytes)
        
        result.setLayout(layout)
        return result
    
    def get_command(self) -> EventCommand:
        obj_id = self.obj_id.get_value()
        jump_bytes = self.jump_bytes.get_value()
        
        if obj_id is None or jump_bytes is None:
            raise CommandError("Invalid input")
            
        return EventCommand.check_drawn(obj_id, jump_bytes)
        
    def apply_arguments(self, command: int, args: list):
        if len(args) >= 2:
            self.obj_id.set_value(args[0])
            self.jump_bytes.set_value(args[1])
