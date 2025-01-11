from editorui.menus.BaseCommandMenu import BaseCommandMenu
from editorui.menus.ValidatingLineEdit import ValidatingLineEdit
from eventcommand import EventCommand

from PyQt6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget


class CheckPartyMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()

        # Check type selector
        type_label = QLabel("Check Type:")
        self.check_type = QComboBox()
        self.check_type.addItem("Check if Active")
        self.check_type.addItem("Check if Recruited")

        # PC Selection dropdown
        pc_label = QLabel("Character:")
        self.pc_id = QComboBox()
        self.pc_id.addItem("Crono", 0)
        self.pc_id.addItem("Marle", 1)
        self.pc_id.addItem("Lucca", 2)
        self.pc_id.addItem("Robo", 3)
        self.pc_id.addItem("Frog", 4)
        self.pc_id.addItem("Ayla", 5)
        self.pc_id.addItem("Magus", 6)

        # Jump bytes input
        jump_label = QLabel("Jump Bytes:")
        self.jump_bytes = ValidatingLineEdit(min_value=0, max_value=0xFF)

        layout.addWidget(type_label)
        layout.addWidget(self.check_type)
        layout.addWidget(pc_label)
        layout.addWidget(self.pc_id)
        layout.addWidget(jump_label)
        layout.addWidget(self.jump_bytes)

        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        pc_id = self.pc_id.currentData()
        jump_bytes = self.jump_bytes.get_value()

        if self.check_type.currentIndex() == 0:
            return EventCommand.check_active_pc(pc_id, jump_bytes)
        else:
            return EventCommand.check_recruited_pc(pc_id, jump_bytes)

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 2:
            if command == 0xD2:
                self.check_type.setCurrentIndex(0)  # Active
            else:
                self.check_type.setCurrentIndex(1)  # Recruited
            self.pc_id.setCurrentIndex(args[0])
            self.jump_bytes.set_value(args[1])