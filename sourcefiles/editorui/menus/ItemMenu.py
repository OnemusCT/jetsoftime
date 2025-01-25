from editorui.menus.BaseCommandMenu import BaseCommandMenu
from editorui.menus.ValidatingLineEdit import ValidatingLineEdit
from eventcommand import EventCommand


from PyQt6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget


class ItemMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()

        self.mode = QComboBox()
        self.mode.addItem("Add Item")
        self.mode.addItem("Remove Item")
        self.mode.addItem("Check Item")

        item_label = QLabel("Item ID")
        self.item_id = ValidatingLineEdit(min_value=0, max_value=0xFF)

        jump_label = QLabel("Jump Bytes (for Check)")
        self.jump_bytes = ValidatingLineEdit(min_value=0, max_value=0xFF)

        self.mode.currentIndexChanged.connect(self._on_mode_changed)

        layout.addWidget(self.mode)
        layout.addWidget(item_label)
        layout.addWidget(self.item_id)
        layout.addWidget(jump_label)
        layout.addWidget(self.jump_bytes)

        result.setLayout(layout)
        self._on_mode_changed(0)  # Initialize state
        return result

    def _on_mode_changed(self, index):
        # Only show jump bytes for check mode
        self.jump_bytes.setEnabled(index == 2)

    def get_command(self) -> EventCommand:
        try:
            item_id = int(self.item_id.text(), 16)
            mode = self.mode.currentIndex()
            if mode == 0:
                return EventCommand.add_item(item_id)
            elif mode == 1:
                return EventCommand.remove_item(item_id)
            else:
                jump_bytes = int(self.jump_bytes.text(), 16)
                return EventCommand.check_item(item_id, jump_bytes)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.item_id.setText(f"{args[0]:02X}")
            if command == 0xCA:
                self.mode.setCurrentIndex(0)
            elif command == 0xCB:
                self.mode.setCurrentIndex(1)
            elif command == 0xC9:
                self.mode.setCurrentIndex(2)
                if len(args) > 1:
                    self.jump_bytes.setText(f"{args[1]:02X}")