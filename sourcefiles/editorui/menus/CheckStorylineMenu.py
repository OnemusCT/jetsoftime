from editorui.menus.BaseCommandMenu import BaseCommandMenu
from editorui.menus.ValidatingLineEdit import ValidatingLineEdit
from eventcommand import EventCommand

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

class CheckStorylineMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()

        # Storyline value input
        value_label = QLabel("Storyline Value:")
        self.storyline_value = ValidatingLineEdit(min_value=0, max_value=0xFF)

        # Jump bytes input
        jump_label = QLabel("Jump Bytes:")
        self.jump_bytes = ValidatingLineEdit(min_value=0, max_value=0xFF)

        layout.addWidget(value_label)
        layout.addWidget(self.storyline_value)
        layout.addWidget(jump_label)
        layout.addWidget(self.jump_bytes)

        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        storyline_val = self.storyline_value.get_value()
        jump_bytes = self.jump_bytes.get_value()
        return EventCommand.if_storyline_counter_lt(storyline_val, jump_bytes)

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 2:
            self.storyline_value.set_value(args[0])
            self.jump_bytes.set_value(args[1])