from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import QApplication, QLineEdit, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QComboBox, QPushButton, QLabel, QGridLayout
from eventcommand import EventCommand

class CommandMenu:
    def command_widget(self) -> QWidget:
        pass

    def get_command(self) -> EventCommand:
        pass

class MemToMemMenu(CommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        from_label = QLabel("From Address")
        self.from_addr = QLineEdit()
        hex_validator = HexValidator()
        self.from_addr.setValidator(hex_validator)

        to_label = QLabel("To Address")
        self.to_addr = QLineEdit()
        self.to_addr.setValidator(hex_validator)

        num_bytes_label = QLabel("Num Bytes")
        self.num_bytes = QComboBox()
        self.num_bytes.addItem("1", 1)
        self.num_bytes.addItem("2", 2)
        #num_bytes.setItemData(0, 1)
        layout.addWidget(from_label)
        layout.addWidget(self.from_addr)

        layout.addWidget(to_label)
        layout.addWidget(self.to_addr)

        layout.addWidget(num_bytes_label)
        layout.addWidget(self.num_bytes)

        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            from_addr = int(self.from_addr.text(), 16)
            to_addr = int(self.to_addr.text(), 16)
            num_bytes = self.num_bytes.currentData()
            return EventCommand.assign_mem_to_mem(from_addr, to_addr, num_bytes)
        except ValueError:
            print("ERROR")

class HexValidator(QValidator):
    def validate(self, text, pos):
        if text == "":
            return QValidator.State.Intermediate, text, pos
        try:
            int(text, 16)
            return QValidator.State.Acceptable, text, pos
        except ValueError:
            return QValidator.State.Invalid, text, pos

def mem_to_mem() -> QWidget:
    result = QWidget()
    layout = QVBoxLayout()
    from_label = QLabel("From Address")
    from_addr = QLineEdit()
    hex_validator = HexValidator()
    from_addr.setValidator(hex_validator)

    to_label = QLabel("To Address")
    to_addr = QLineEdit()
    to_addr.setValidator(hex_validator)

    num_bytes_label = QLabel("Num Bytes")
    num_bytes = QComboBox()
    num_bytes.addItem("1", 1)
    num_bytes.addItem("2", 2)
    #num_bytes.setItemData(0, 1)
    layout.addWidget(from_label)
    layout.addWidget(from_addr)

    layout.addWidget(to_label)
    layout.addWidget(to_addr)

    layout.addWidget(num_bytes_label)
    layout.addWidget(num_bytes)

    result.setLayout(layout)
    return result