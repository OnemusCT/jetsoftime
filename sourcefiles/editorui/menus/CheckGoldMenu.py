from editorui.menus.BaseCommandMenu import BaseCommandMenu
from editorui.menus.ValidatingLineEdit import ValidatingLineEdit
from eventcommand import EventCommand


from PyQt6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget


class CheckGoldMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()

        amount_label = QLabel("Gold Amount")
        self.amount = ValidatingLineEdit(min_value=0, max_value=0xFFFF)

        jump_label = QLabel("Jump Bytes if Not Enough")
        self.jump_bytes = QLineEdit()
        jump_validator = ValidatingLineEdit(min_value=0, max_value=0xFF)
        self.jump_bytes.setValidator(jump_validator)

        layout.addWidget(amount_label)
        layout.addWidget(self.amount)
        layout.addWidget(jump_label)
        layout.addWidget(self.jump_bytes)

        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            amount = int(self.amount.text(), 16)
            jump_bytes = int(self.jump_bytes.text(), 16)
            return EventCommand.check_gold(amount, jump_bytes)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 2:
            self.amount.setText(f"{args[0]:04X}")
            self.jump_bytes.setText(f"{args[1]:02X}")