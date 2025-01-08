from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLineEdit, QVBoxLayout, QWidget, QComboBox, QLabel, QGridLayout, QCheckBox, QHBoxLayout
from eventcommand import EventCommand, event_commands
from commandgroups import EventCommandType, EventCommandSubtype


_byte_commands = [
    0x4F,  # assignment with value
    0x51,  # mem-to-mem assignment
    0x53,  # assignment from address
    0x58,  # inverse assignment
    0x5D,  # add operation
    0x5F,  # subtract operation
    0x71,  # increment
    0x75,  # set byte
    0x4C,  # loads one byte
]

_word_commands = [
    0x50,  # two byte version of 4F
    0x52,  # two byte version of 51
    0x54,  # two byte version of 53
    0x59,  # two byte version of 58
    0x5E,  # two byte version of 5D
    0x60,  # two byte version of 5F
    0x72,  # two byte version of 71
    0x76,  # two byte version of 75
    0x4D,  # loads two bytes
]

from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import QLineEdit, QLabel
from PyQt6.QtCore import Qt, pyqtSignal

from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal

class ValidatingLineEdit(QLineEdit):
    """A QLineEdit that validates hex input and shows error tooltips."""
    
    validationChanged = pyqtSignal(bool)  # Emits True if valid, False if invalid
    
    def __init__(self, min_value=0, max_value=None, parent=None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value if max_value is not None else float('inf')
        
        # Connect focus events
        self.focusOutEvent = self._handle_focus_out
        
    def set_error(self, message):
        """Show an error message as a tooltip and highlight the field."""
        self.setStyleSheet("border: 2px solid #ff6b6b;")
        self.setToolTip(message)
        self.validationChanged.emit(False)
        
    def clear_error(self):
        """Clear any displayed error."""
        self.setStyleSheet("")
        self.setToolTip("")
        self.validationChanged.emit(True)
        
    def _handle_focus_out(self, event):
        """Validate input when focus is lost."""
        text = self.text().strip()
        
        # Empty is invalid if we have a minimum
        if not text:
            if self.min_value > 0:
                self.set_error(f"Value required (min: {self.min_value:X})")
            else:
                self.clear_error()
            super().focusOutEvent(event)
            return
            
        # Try parsing the hex value
        try:
            value = int(text, 16)
            if value < self.min_value:
                self.set_error(f"Value must be at least {self.min_value:X}")
            elif value > self.max_value:
                self.set_error(f"Value must be no more than {self.max_value:X}")
            else:
                self.clear_error()
        except ValueError:
            self.set_error("Invalid hexadecimal value")
            
        super().focusOutEvent(event)
        
    def get_value(self):
        """Get the current value as an integer, or None if invalid."""
        try:
            value = int(self.text(), 16)
            if self.min_value <= value <= self.max_value:
                return value
        except ValueError:
            pass
        return None
        
    def set_value(self, value):
        """Set the value, formatting it as hex."""
        if value is not None:
            self.setText(f"{value:X}")
            self.clear_error()
        else:
            self.clear()

class CommandError(Exception):
    """Exception raised for command menu errors."""
    pass

class BaseCommandMenu:
    """Base class for command menus with error handling."""
    
    def __init__(self):
        pass
        
    def validate(self):
        """Validate all inputs. Returns True if valid, False if not."""
        return True  # Override in subclasses
        
    def safe_get_command(self):
        """Get the command, handling any errors."""
        try:
            if not self.validate():
                return None
            return self.get_command()
        except CommandError as e:
            # Find all ValidatingLineEdit widgets and set their tooltips
            widget = self.command_widget()
            error_shown = False
            for child in widget.findChildren(ValidatingLineEdit):
                if child.get_value() is None:
                    child.set_error(str(e))
                    error_shown = True
            # If no specific field was invalid, set tooltip on first input
            if not error_shown:
                first_input = widget.findChild(ValidatingLineEdit)
                if first_input:
                    first_input.set_error(str(e))
            return None
        except Exception as e:
            # Handle unexpected errors similarly
            first_input = self.command_widget().findChild(ValidatingLineEdit)
            if first_input:
                first_input.set_error(f"Unexpected error: {str(e)}")
            return None

class UnassignedMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        return QWidget()

    def get_command(self) -> EventCommand:
        return event_commands[1]

    def apply_arguments(self, command, args):
        pass

class EquipItemMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        pc_label = QLabel("PC ID")
        self.pc_id = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        item_label = QLabel("Item ID")
        self.item_id = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        layout.addWidget(pc_label)
        layout.addWidget(self.pc_id)
        layout.addWidget(item_label)
        layout.addWidget(self.item_id)
        
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            pc_id = int(self.pc_id.text(), 16)
            item_id = int(self.item_id.text(), 16)
            return EventCommand.equip_item(pc_id, item_id)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 2:
            self.pc_id.setText(f"{args[0]:02X}")
            self.item_id.setText(f"{args[1]:02X}")

class GetItemQuantityMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        item_label = QLabel("Item ID")
        self.item_id = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        addr_label = QLabel("Store To Address")
        self.store_addr = ValidatingLineEdit(min_value=0x7F0200, max_value=0x7F0400)
        
        layout.addWidget(item_label)
        layout.addWidget(self.item_id)
        layout.addWidget(addr_label)
        layout.addWidget(self.store_addr)
        
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            item_id = int(self.item_id.text(), 16)
            store_addr = int(self.store_addr.text(), 16)
            return EventCommand.get_item_quantity(item_id, store_addr)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 2:
            self.item_id.setText(f"{args[0]:02X}")
            self.store_addr.setText(f"{0x7F0200 + args[1]*2:06X}")

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

class AddGoldMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        amount_label = QLabel("Gold Amount")
        self.amount = ValidatingLineEdit(min_value=0, max_value=0xFFFF)
        
        self.add_mode = QComboBox()
        self.add_mode.addItem("Add Gold")
        self.add_mode.addItem("Remove Gold")
        
        layout.addWidget(self.add_mode)
        layout.addWidget(amount_label)
        layout.addWidget(self.amount)
        
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            amount = int(self.amount.text(), 16)
            if self.add_mode.currentIndex() == 0:
                return EventCommand.add_gold(amount)
            else:
                return EventCommand.remove_gold(amount) 
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.amount.setText(f"{args[0]:04X}")
            # Set mode based on command
            self.add_mode.setCurrentIndex(0 if command == 0xCD else 1)

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

class ItemFromMemMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        addr_label = QLabel("Item ID Address")
        self.addr = ValidatingLineEdit(min_value=0x7F0200, max_value=0x7F0400)
        
        layout.addWidget(addr_label)
        layout.addWidget(self.addr)
        
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            addr = int(self.addr.text(), 16)
            return EventCommand.add_item_from_mem(addr)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.addr.setText(f"{0x7F0200 + args[0]*2:06X}")

class StringIndexMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        addr_label = QLabel("ROM Address")
        self.address = ValidatingLineEdit(min_value=0, max_value=0xFFFFFF)
        
        layout.addWidget(addr_label)
        layout.addWidget(self.address)
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            address = int(self.address.text(), 16)
            return EventCommand.string_index(address)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.address.setText(f"{args[0]:06X}")

class SpecialDialogMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        self.mode = QComboBox()
        self.mode.addItem("Replace Characters")
        self.mode.addItem("Rename Character")
        self.mode.addItem("Custom Dialog ID")
        
        self.dialog_id = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        self.char_id = QComboBox()
        for i in range(8):  # 0-7 for different characters
            self.char_id.addItem(f"Character {i}")
            
        self.mode.currentIndexChanged.connect(self._on_mode_changed)
        
        layout.addWidget(self.mode)
        layout.addWidget(self.dialog_id)
        layout.addWidget(self.char_id)
        
        result.setLayout(layout)
        self._on_mode_changed(0)  # Initialize state
        return result

    def _on_mode_changed(self, index):
        self.dialog_id.setVisible(index == 2)
        self.char_id.setVisible(index == 1)

    def get_command(self) -> EventCommand:
        try:
            mode = self.mode.currentIndex()
            if mode == 0:
                return EventCommand.replace_characters()
            elif mode == 1:
                return EventCommand.rename_character(self.char_id.currentIndex())
            else:
                dialog_id = int(self.dialog_id.text(), 16)
                return EventCommand.special_dialog(dialog_id)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            arg = args[0]
            if arg == 0:
                self.mode.setCurrentIndex(0)  # Replace characters
            elif (arg & 0xC0) == 0xC0:
                self.mode.setCurrentIndex(1)  # Rename character
                self.char_id.setCurrentIndex(arg & 0x3F)
            else:
                self.mode.setCurrentIndex(2)  # Custom dialog
                self.dialog_id.setText(f"{arg:02X}")

class TextboxMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        string_label = QLabel("String ID")
        self.string_id = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        self.box_type = QComboBox()
        self.box_type.addItem("Auto-positioned")
        self.box_type.addItem("Top")
        self.box_type.addItem("Bottom")
        self.box_type.addItem("Auto-positioned (Top)")
        self.box_type.addItem("Auto-positioned (Bottom)")
        self.box_type.addItem("Personal")
        
        self.first_line = QComboBox()
        self.last_line = QComboBox()
        for i in range(4):
            self.first_line.addItem(f"Line {i}")
            self.last_line.addItem(f"Line {i}")
            
        self.box_type.currentIndexChanged.connect(self._on_type_changed)
        
        layout.addWidget(string_label)
        layout.addWidget(self.string_id)
        layout.addWidget(self.box_type)
        layout.addWidget(QLabel("First Line"))
        layout.addWidget(self.first_line)
        layout.addWidget(QLabel("Last Line"))
        layout.addWidget(self.last_line)
        
        result.setLayout(layout)
        self._on_type_changed(0)  # Initialize state
        return result

    def _on_type_changed(self, index):
        # Show line selection only for auto-positioned types
        needs_lines = index in [0, 3, 4]
        self.first_line.setVisible(needs_lines)
        self.last_line.setVisible(needs_lines)

    def get_command(self) -> EventCommand:
        try:
            string_id = int(self.string_id.text(), 16)
            box_type = self.box_type.currentIndex()
            
            if box_type == 0:  # Auto
                return EventCommand.textbox_auto(string_id, 
                                              self.first_line.currentIndex(),
                                              self.last_line.currentIndex())
            elif box_type == 1:  # Top
                return EventCommand.textbox_top(string_id)
            elif box_type == 2:  # Bottom
                return EventCommand.textbox_bottom(string_id)
            elif box_type == 3:  # Auto Top
                return EventCommand.textbox_auto_top(string_id,
                                                  self.first_line.currentIndex(),
                                                  self.last_line.currentIndex())
            elif box_type == 4:  # Auto Bottom
                return EventCommand.textbox_auto_bottom(string_id,
                                                    self.first_line.currentIndex(),
                                                    self.last_line.currentIndex())
            else:  # Personal
                return EventCommand.personal_textbox(string_id)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.string_id.setText(f"{args[0]:02X}")
            
            if command == 0xBB:  # Personal
                self.box_type.setCurrentIndex(5)
            elif command == 0xC0:  # Auto
                self.box_type.setCurrentIndex(0)
                if len(args) > 1:
                    self.first_line.setCurrentIndex(args[1] >> 2)
                    self.last_line.setCurrentIndex(args[1] & 0x03)
            elif command == 0xC1:  # Top
                self.box_type.setCurrentIndex(1)
            elif command == 0xC2:  # Bottom
                self.box_type.setCurrentIndex(2)
            elif command == 0xC3:  # Auto Top
                self.box_type.setCurrentIndex(3)
                if len(args) > 1:
                    self.first_line.setCurrentIndex(args[1] >> 2)
                    self.last_line.setCurrentIndex(args[1] & 0x03)
            elif command == 0xC4:  # Auto Bottom
                self.box_type.setCurrentIndex(4)
                if len(args) > 1:
                    self.first_line.setCurrentIndex(args[1] >> 2)
                    self.last_line.setCurrentIndex(args[1] & 0x03)

class AnimationMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        # Animation ID input with validation
        animation_label = QLabel("Animation ID")
        self.animation_id = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        # Loops input with validation
        loops_label = QLabel("Loops")
        self.loops = ValidatingLineEdit(min_value=0, max_value=0xFF)
        self.loops.setText("0")
        self.loops.setDisabled(True)
        
        # Animation type selector
        type_label = QLabel("Type")
        self.type = QComboBox()
        self.type.addItem("Normal")
        self.type.addItem("Static")
        self.type.addItem("Loop")
        self.type.setCurrentIndex(0)
        self.type.currentIndexChanged.connect(self._on_index_changed)
        
        # Add components to layout
        layout.addWidget(animation_label)
        layout.addWidget(self.animation_id)
        layout.addWidget(type_label)
        layout.addWidget(self.type)
        layout.addWidget(loops_label)
        layout.addWidget(self.loops)
        
        result.setLayout(layout)
        return result
        
    def validate(self) -> bool:
        """Validate all inputs before creating command."""
        self.clear_error()
        
        # Check animation ID
        if self.animation_id.get_value() is None:
            return False
            
        # Check loops if in loop mode
        if self.type.currentText() == "Loop" and not self.loops.isEnabled():
            if self.loops.get_value() is None:
                return False
                
        return True

    def get_command(self) -> EventCommand:
        animation_id = self.animation_id.get_value()
        if animation_id is None:
            raise CommandError("Invalid animation ID")
            
        anim_type = self.type.currentText()
        loops = self.loops.get_value() if self.loops.isEnabled() else 0
        
        if anim_type == "Loop" and loops is None:
            raise CommandError("Invalid loop count")
            
        return EventCommand.animation(animation_id, anim_type, loops)

    def apply_arguments(self, command: int, args: list):
        # Handle special cases B3 and B4 (hard-coded animation IDs)
        if command == 0xB3:
            self.animation_id.set_value(0)
            self.type.setCurrentText("Normal")
            self.loops.set_value(0)
            return
        elif command == 0xB4:
            self.animation_id.set_value(1)
            self.type.setCurrentText("Normal")
            self.loops.set_value(0)
            return

        # Handle other commands
        if command == 0xAA:  # Infinite loop
            self.animation_id.set_value(args[0])
            self.type.setCurrentText("Loop")
            self.loops.set_value(0)
        elif command == 0xAB:  # Normal animation
            self.animation_id.set_value(args[0])
            self.type.setCurrentText("Normal")
            self.loops.set_value(0)
        elif command == 0xAC:  # Static animation
            self.animation_id.set_value(args[0])
            self.type.setCurrentText("Static")
            self.loops.set_value(0)
        elif command == 0xB7:  # Specified loop count
            self.animation_id.set_value(args[0])
            self.type.setCurrentText("Loop")
            self.loops.set_value(args[1])

    def _on_index_changed(self, index):
        self.loops.setEnabled(self.type.currentText() == "Loop")
        if not self.loops.isEnabled():
            self.loops.setText("0")
            self.loops.clear_error()

class AnimationLimiterMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        limit_label = QLabel("Animation Limit")
        self.limit = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        layout.addWidget(limit_label)
        layout.addWidget(self.limit)
        
        result.setLayout(layout)
        return result
    
    def get_command(self) -> EventCommand:
        try:
            limit = int(self.limit.text(), 16)
            return EventCommand.animation_limiter(limit)
        except ValueError:
            print("ERROR")
            
    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.limit.setText(f"{args[0]:02X}")

class GetStoryCtrMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        addr_label = QLabel("Destination (7F0200-7F0400)")
        self.addr = ValidatingLineEdit(min_value=0x7F0200, max_value=0x7F0400)
        self.addr.setText("7F0200")
        
        layout.addWidget(addr_label)
        layout.addWidget(self.addr)
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            addr = int(self.addr.text(), 16)
            return EventCommand.get_storyline(addr)
        except ValueError as e:
            print(e)

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.addr.setText("{:02X}".format(args[0]*2 + 0x7F0200))

class GetPC1Menu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        address_label = QLabel("Destination Address")
        self.address = ValidatingLineEdit(min_value=0x7F0200, max_value=0x7F0400)
        
        layout.addWidget(address_label)
        layout.addWidget(self.address)
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            address = int(self.address.text(), 16)
            return EventCommand.get_pc1(address)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.address.setText("{:02X}".format(args[0]*2 + 0x7F0200))

class RandomNumberMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        address_label = QLabel("Destination Address")
        self.address = ValidatingLineEdit(min_value=0x7F0200, max_value=0x7F0400)
        
        layout.addWidget(address_label)
        layout.addWidget(self.offset)
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            address = int(self.address.text(), 16)
            return EventCommand.random_number(address)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.address.setText("{:02X}".format(args[0]*2 + 0x7F0200))

class LoadASCIIMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        index_label = QLabel("ASCII Index")
        self.index = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        layout.addWidget(index_label)
        layout.addWidget(self.index)
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            index = int(self.index.text(), 16)
            return EventCommand.load_ascii(index)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.index.setText(f"{args[0]:02X}")

class ChangePaletteMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        palette_label = QLabel("Palette ID")
        self.palette = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        layout.addWidget(palette_label)
        layout.addWidget(self.palette)
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            palette = int(self.palette.text(), 16)
            return EventCommand.change_palette(palette)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.palette.setText(f"{args[0]:02X}")

class ScriptSpeedMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        speed_label = QLabel("Script Speed (0=fastest, 80=stop)")
        self.speed = ValidatingLineEdit(min_value=0, max_value=0x80)
        
        layout.addWidget(speed_label)
        layout.addWidget(self.speed)
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            speed = int(self.speed.text(), 16)
            return EventCommand.script_speed(speed)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.speed.setText(f"{args[0]:02X}")

class SpriteCollisionMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        props_label = QLabel("Solidity Properties")
        self.props = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        layout.addWidget(props_label)
        layout.addWidget(self.props)
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            props = int(self.props.text(), 16)
            return EventCommand.sprite_collision(props)
        except ValueError:
            print("ERROR")

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.props.setText(f"{args[0]:02X}")

class ExploreModeMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        explore_label = QLabel("Explore Mode")
        self.explore_mode = QComboBox()
        self.explore_mode.addItem("On")
        self.explore_mode.addItem("Off")
        self.explore_mode.setCurrentIndex(0)

        layout.addWidget(explore_label)
        layout.addWidget(self.explore_mode)

        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
       return EventCommand.set_explore_mode(self.explore_mode.currentIndex() == 0)
           

    def apply_arguments(self, command: int, args: list):
        if args[0] == 1:
            self.explore_mode.setCurrentIndex(0)
        else:
            self.explore_mode.setCurrentIndex(1)

class ControllableMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        controllable_label = QLabel("Controllable")
        self.controllable = QComboBox()
        self.controllable.addItem("Once")
        self.controllable.addItem("Infinite")
        self.controllable.setCurrentIndex(0)

        layout.addWidget(controllable_label)
        layout.addWidget(self.controllable)

        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
       if self.controllable.currentIndex() == 0:
           return EventCommand.set_controllable_once()
       return EventCommand.set_controllable_infinite()
           

    def apply_arguments(self, command: int, args: list):
        if command == 0xAF:
            self.controllable.setCurrentIndex(0)
        else:
            self.controllable.setCurrentIndex(1)

class ValToMemAssignMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        value_label = QLabel("Value")
        self.value = ValidatingLineEdit(min_value=0, max_value=0xFFFF)
        
        addr_label = QLabel("Destination Address")
        self.dest_addr = ValidatingLineEdit(min_value=0x7E0000, max_value=0x7FFFFF)
        
        size_label = QLabel("Size")
        self.size = QComboBox()
        self.size.addItem("Byte", 1)
        self.size.addItem("Word", 2)
        
        layout.addWidget(value_label)
        layout.addWidget(self.value)
        layout.addWidget(addr_label)
        layout.addWidget(self.dest_addr)
        layout.addWidget(size_label)
        layout.addWidget(self.size)
        
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            value = int(self.value.text(), 16)
            dest_addr = int(self.dest_addr.text(), 16)
            return EventCommand.assign_val_to_mem(value, dest_addr, self.size.currentData())
        except ValueError as e:
            print(f"ERROR: {e}")

    def apply_arguments(self, command: int, args: list):
        if len(args) < 2:
            return
            
        # Decode based on command type
        if command in [0x4A, 0x4B]:  # Any memory address
            value = args[1]
            dest_addr = args[0]
        elif command in [0x4F, 0x50]:  # Script memory
            value = args[0]
            dest_addr = 0x7F0200 + (args[1] * 2)
        else:  # 0x56 - Bank 7F
            value = args[0]
            dest_addr = 0x7F0000 + args[1]
            
        self.value.setText(f"{value:X}")
        self.dest_addr.setText(f"{dest_addr:06X}")
        
        # Set size based on command
        if command in [0x4A, 0x4F, 0x56]:  # Byte commands
            self.size.setCurrentIndex(0)
        else:  # Word commands
            self.size.setCurrentIndex(1)

class GetResultMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        addr_label = QLabel("Store To Address")
        self.addr = ValidatingLineEdit(min_value=0x7F0000, max_value=0x7FFFFF)
        
        layout.addWidget(addr_label)
        layout.addWidget(self.addr)
        
        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            addr = int(self.addr.text(), 16)
            return EventCommand.get_result(addr)
        except ValueError as e:
            print(f"ERROR: {e}")

    def apply_arguments(self, command: int, args: list):
        if len(args) == 0:
            return
            
        if command == 0x19:  # Script memory
            addr = 0x7F0200 + (args[0] * 2)
        else:  # 0x1C - Local memory
            addr = 0x7F0000 + args[0]
            
        self.addr.setText(f"{addr:06X}")

class MemToMemAssignMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        from_label = QLabel("From Address")
        self.source_addr = ValidatingLineEdit(min_value=0x7F0000, max_value=0x7FFFFF)

        to_label = QLabel("To Address")
        self.dest_addr = ValidatingLineEdit(min_value=0x7F0000, max_value=0x7FFFFF)

        num_bytes_label = QLabel("Size")
        self.num_bytes = QComboBox()
        self.num_bytes.addItem("Byte", 1)
        self.num_bytes.addItem("Word", 2)
        #num_bytes.setItemData(0, 1)
        layout.addWidget(from_label)
        layout.addWidget(self.source_addr)

        layout.addWidget(to_label)
        layout.addWidget(self.dest_addr)

        layout.addWidget(num_bytes_label)
        layout.addWidget(self.num_bytes)

        result.setLayout(layout)
        return result

    def get_command(self) -> EventCommand:
        try:
            source_addr = int(self.source_addr.text(), 16)
            dest_addr = int(self.dest_addr.text(), 16)
            num_bytes = self.num_bytes.currentData()
            return EventCommand.assign_mem_to_mem(source_addr, dest_addr, num_bytes)
        except ValueError:
            print("ERROR")
    
    def apply_arguments(self, command, args):
        if command == 0x48 or command == 0x49:
            # 48: aaaaaa - address to load from, oo - offset to store to (*2, +7F0200)
            # 49: aaaaaa - address to load from, oo - offset to store to (/2 +7F0200)
            source_addr = args[0]
            if command == 0x48:
                dest_addr = 0x7F0200 + (args[1] * 2)
            else:  # 0x49
                dest_addr = 0x7F0200 + (args[1] // 2)
        elif command == 0x4C or command == 0x4D:
            # 4C: aaaaaa - address to store to, oo - offset to load from (*2, +7F0200)
            # 4D: aaaaaa - address to store to, oo - offset to load from (*2, +7F0200)
            source_addr = 0x7F0200 + (args[1] * 2)
            dest_addr = args[0]

        elif command == 0x51 or command == 0x52:
            # 51/52: aa - offset to load from (*2, +7F0200), oo - offset to store to (*2, +7F0200)
            source_addr = 0x7F0200 + (args[0] * 2)
            dest_addr = 0x7F0200 + (args[1] * 2)

        elif command == 0x53 or command == 0x54:
            # 53/54: aaaa - address to load from (+7F0000), oo - offset to store to (*2, +7F0200)
            source_addr = 0x7F0000 + args[0]
            dest_addr = 0x7F0200 + (args[1] * 2)

        else:  # 0x58 or 0x59
            # 58/59: oo - offset to load from (*2, +7F0200), aaaa - address to store to (+7F0000)
            source_addr = 0x7F0200 + (args[0] * 2)
            dest_addr = 0x7F0000 + args[1]

        self.source_addr.setText("{:02X}".format(source_addr))
        self.dest_addr.setText("{:02X}".format(dest_addr))
        if command in _byte_commands:
            self.num_bytes.setCurrentIndex(0)
        elif command in _word_commands:
            self.num_bytes.setCurrentIndex(1)
        else:
            print("ERROR!!!")

class ResultMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        addr_label = QLabel("Store To Address")
        self.addr = ValidatingLineEdit(min_value=0x7F0000, max_value=0x7FFFFF)
        self.addr.setPlaceholderText("Enter address (e.g. 7F0200)")
        
        layout.addWidget(addr_label)
        layout.addWidget(self.addr)
        
        result.setLayout(layout)
        return result

    def validate(self) -> bool:
        if self.addr.get_value() is None:
            return False
        return True

    def get_command(self) -> EventCommand:
        addr = self.addr.get_value()
        if addr is None:
            raise CommandError("Invalid address value")
        return EventCommand.get_result(addr)

    def apply_arguments(self, command: int, args: list):
        if len(args) == 0:
            return
            
        if command == 0x19:  # Script memory
            addr = 0x7F0200 + (args[0] * 2)
        else:  # 0x1C - Local memory
            addr = 0x7F0000 + args[0]
            
        self.addr.set_value(addr)

class SetStorylineMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        value_label = QLabel("Storyline Value")
        self.value = ValidatingLineEdit(min_value=0, max_value=0xFF)
        self.value.setPlaceholderText("Enter value (0-FF)")
        
        layout.addWidget(value_label)
        layout.addWidget(self.value)
        
        result.setLayout(layout)
        return result

    def validate(self) -> bool:
        if self.value.get_value() is None:
            return False
        return True

    def get_command(self) -> EventCommand:
        value = self.value.get_value()
        if value is None:
            raise CommandError("Invalid storyline value")
        return EventCommand.set_storyline_counter(value)

    def apply_arguments(self, command: int, args: list):
        if len(args) > 0:
            self.value.set_value(args[0])

class ResetAnimationMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        # Since this command takes no arguments, we'll just show a label
        result = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("Reset Animation Command")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description = QLabel("Resets the current object's animation")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(label)
        layout.addWidget(description)
        
        result.setLayout(layout)
        return result

    def validate(self) -> bool:
        return True  # Always valid since no inputs

    def get_command(self) -> EventCommand:
        return EventCommand.reset_animation()

    def apply_arguments(self, command: int, args: list):
        pass  # No arguments to apply

class BattleMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        # Create grid layout for checkboxes
        grid = QGridLayout()
        
        # All flags in a simple list
        self.flags = [
            ('no_win_pose', "No win pose"),
            ('bottom_menu', "Bottom menu"),
            ('small_pc_sol', "Small PC Sol."),
            ('unused_108', "Unused 1.08"),
            ('static_enemies', "Static enemies"),
            ('special_event', "Special event"),
            ('unknown_140', "Unknown 1.40"),
            ('no_run', "No run"),
            ('unknown_201', "Unknown 2.01"),
            ('unknown_202', "Unknown 2.02"),
            ('unknown_204', "Unknown 2.04"),
            ('unknown_208', "Unknown 2.08"),
            ('unknown_210', "Unknown 2.10"),
            ('no_game_over', "No game over"),
            ('map_music', "Map music"),
            ('regroup', "Regroup")
        ]
        
        # Add checkboxes in a 2-column grid
        for i, (attr_name, label) in enumerate(self.flags):
            checkbox = QCheckBox(label)
            setattr(self, attr_name, checkbox)
            grid.addWidget(checkbox, i // 2, i % 2)
            checkbox.stateChanged.connect(self._update_hex_display)
        
        # Add hex display of current values
        self.hex_display = QLabel()
        self.hex_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_hex_display()
        
        layout.addLayout(grid)
        layout.addWidget(self.hex_display)
        result.setLayout(layout)
        return result
    
    def _update_hex_display(self):
        """Update the hex display to show current flag values"""
        byte1 = 0
        byte2 = 0
        
        # First byte flags
        for i, (attr_name, _) in enumerate(self.flags[:8]):
            if getattr(self, attr_name).isChecked():
                byte1 |= (1 << i)
                
        # Second byte flags
        for i, (attr_name, _) in enumerate(self.flags[8:]):
            if getattr(self, attr_name).isChecked():
                byte2 |= (1 << i)
        
        self.hex_display.setText(f"Value: {byte1:02X} {byte2:02X}")

    def validate(self) -> bool:
        return True  # Always valid since checkboxes can't have invalid state

    def get_command(self) -> EventCommand:
        return EventCommand.battle(
            **{attr_name: getattr(self, attr_name).isChecked() 
               for attr_name, _ in self.flags}
        )

    def apply_arguments(self, command: int, args: list):
        if len(args) < 2:
            return
            
        # First byte flags
        for i, (attr_name, _) in enumerate(self.flags[:8]):
            getattr(self, attr_name).setChecked(args[0] & (1 << i))
            
        # Second byte flags
        for i, (attr_name, _) in enumerate(self.flags[8:]):
            getattr(self, attr_name).setChecked(args[1] & (1 << i))

class CheckButtonMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        # Check type selection (Action vs Button)
        type_label = QLabel("Check Type:")
        self.check_type = QComboBox()
        self.check_type.addItem("Action")
        self.check_type.addItem("Button")
        self.check_type.currentIndexChanged.connect(self._update_button_choices)
        
        # Button/Action selection
        button_label = QLabel("Button/Action:")
        self.button_choice = QComboBox()
        
        # Current vs Since Last
        mode_label = QLabel("Check Mode:")
        self.check_mode = QComboBox()
        self.check_mode.addItem("Current")
        self.check_mode.addItem("Since Last Check")
        self.check_mode.currentIndexChanged.connect(self._validate_combination)
        
        # Jump bytes
        jump_label = QLabel("Jump Bytes:")
        self.jump_bytes = ValidatingLineEdit(min_value=0, max_value=0xFF)
        self.jump_bytes.setPlaceholderText("Enter jump distance (hex)")
        
        # Command preview
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add everything to layout
        layout.addWidget(type_label)
        layout.addWidget(self.check_type)
        layout.addWidget(button_label)
        layout.addWidget(self.button_choice)
        layout.addWidget(mode_label)
        layout.addWidget(self.check_mode)
        layout.addWidget(jump_label)
        layout.addWidget(self.jump_bytes)
        layout.addWidget(self.preview)
        
        result.setLayout(layout)
        
        # Initialize button choices
        self._update_button_choices(0)
        
        # Connect signals for preview updates
        self.check_type.currentIndexChanged.connect(self._update_preview)
        self.button_choice.currentIndexChanged.connect(self._update_preview)
        self.check_mode.currentIndexChanged.connect(self._update_preview)
        self.jump_bytes.textChanged.connect(self._update_preview)
        
        return result
    
    def _update_button_choices(self, index):
        """Update available button choices based on check type"""
        self.button_choice.clear()
        
        if index == 0:  # Action
            self.button_choice.addItem("Dash")
            self.button_choice.addItem("Confirm")
        else:  # Button
            for button in ["Any", "A", "B", "X", "Y", "L", "R"]:
                self.button_choice.addItem(button)
                
        self._validate_combination()
        
    def _validate_combination(self):
        """Validate the current combination of choices"""
        # "Any" button can't be used with "Since Last Check"
        is_any = (self.check_type.currentText() == "Button" and 
                 self.button_choice.currentText() == "Any")
        is_since_last = self.check_mode.currentIndex() == 1
        
        if is_any and is_since_last:
            self.check_mode.setCurrentIndex(0)
            self.check_mode.setEnabled(False)
        else:
            self.check_mode.setEnabled(True)
            
    def _update_preview(self):
        """Update the command preview"""
        try:
            cmd = self.get_command()
            self.preview.setText(f"Command: {cmd.command:02X}")
            self.preview.setStyleSheet("")
        except (ValueError, CommandError) as e:
            self.preview.setText(str(e))
            self.preview.setStyleSheet("color: red;")

    def validate(self) -> bool:
        """Validate the current input"""
        if self.jump_bytes.get_value() is None:
            return False
            
        # Check for invalid Any + Since Last combination
        is_any = (self.check_type.currentText() == "Button" and 
                 self.button_choice.currentText() == "Any")
        is_since_last = self.check_mode.currentIndex() == 1
        
        if is_any and is_since_last:
            return False
            
        return True

    def get_command(self) -> EventCommand:
        if not self.validate():
            raise CommandError("Invalid button check combination")
            
        is_action = self.check_type.currentText() == "Action"
        button = self.button_choice.currentText()
        since_last = self.check_mode.currentIndex() == 1
        jump_bytes = self.jump_bytes.get_value()
        
        if jump_bytes is None:
            raise CommandError("Invalid jump bytes value")
            
        return EventCommand.check_button(is_action, button, since_last, jump_bytes)

    def apply_arguments(self, command: int, args: list):
        if len(args) < 1:
            return
            
        # Map command to settings
        if command in [0x30, 0x31]:  # Action current
            self.check_type.setCurrentText("Action")
            self.check_mode.setCurrentIndex(0)
            self.button_choice.setCurrentText("Dash" if command == 0x30 else "Confirm")
            
        elif command in [0x3B, 0x3C]:  # Action since last
            self.check_type.setCurrentText("Action")
            self.check_mode.setCurrentIndex(1)
            self.button_choice.setCurrentText("Dash" if command == 0x3B else "Confirm")
            
        elif command == 0x2D:  # Any button current
            self.check_type.setCurrentText("Button")
            self.check_mode.setCurrentIndex(0)
            self.button_choice.setCurrentText("Any")
            
        else:  # Specific button
            self.check_type.setCurrentText("Button")
            
            # Map command to button and mode
            button_map = {
                0x34: ("A", 0), 0x35: ("B", 0), 0x36: ("X", 0),
                0x37: ("Y", 0), 0x38: ("L", 0), 0x39: ("R", 0),
                0x3F: ("A", 1), 0x40: ("B", 1), 0x41: ("X", 1),
                0x42: ("Y", 1), 0x43: ("L", 1), 0x44: ("R", 1)
            }
            
            if command in button_map:
                button, mode = button_map[command]
                self.button_choice.setCurrentText(button)
                self.check_mode.setCurrentIndex(mode)
        
        # Set jump bytes
        self.jump_bytes.set_value(args[0])

class MovePartyMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QGridLayout()
        
        # Create inputs for each PC's coordinates
        self.coords = []
        for i in range(3):
            pc_label = QLabel(f"PC{i+1} Position:")
            x_label = QLabel("X:")
            y_label = QLabel("Y:")
            
            x_input = ValidatingLineEdit(min_value=0, max_value=0xFF)
            y_input = ValidatingLineEdit(min_value=0, max_value=0xFF)
            
            layout.addWidget(pc_label, i*2, 0)
            layout.addWidget(x_label, i*2+1, 0)
            layout.addWidget(x_input, i*2+1, 1)
            layout.addWidget(y_label, i*2+1, 2)
            layout.addWidget(y_input, i*2+1, 3)
            
            self.coords.append((x_input, y_input))
        
        result.setLayout(layout)
        return result
        
    def validate(self) -> bool:
        return all(x.get_value() is not None and y.get_value() is not None 
                  for x, y in self.coords)

    def get_command(self) -> EventCommand:
        if not self.validate():
            raise CommandError("All coordinates must be valid")
        
        coords = []
        for x_input, y_input in self.coords:
            coords.extend([x_input.get_value(), y_input.get_value()])
            
        return EventCommand.move_party(*coords)

    def apply_arguments(self, command: int, args: list):
        if len(args) < 6:
            return
            
        for i, (x_input, y_input) in enumerate(self.coords):
            x_input.set_value(args[i*2])
            y_input.set_value(args[i*2+1])

class VectorMoveMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        # Angle input (0-255 maps to 0-360 degrees)
        angle_layout = QHBoxLayout()
        angle_label = QLabel("Angle (degrees):")
        self.angle_input = ValidatingLineEdit(min_value=0, max_value=359)
        angle_layout.addWidget(angle_label)
        angle_layout.addWidget(self.angle_input)
        
        # Magnitude input
        mag_layout = QHBoxLayout()
        mag_label = QLabel("Magnitude:")
        self.mag_input = ValidatingLineEdit(min_value=0, max_value=0xFF)
        mag_layout.addWidget(mag_label)
        mag_layout.addWidget(self.mag_input)
        
        # Keep facing checkbox
        self.keep_facing = QCheckBox("Keep current facing")
        
        layout.addLayout(angle_layout)
        layout.addLayout(mag_layout)
        layout.addWidget(self.keep_facing)
        result.setLayout(layout)
        return result
        
    def validate(self) -> bool:
        return (self.angle_input.get_value() is not None and 
                self.mag_input.get_value() is not None)

    def get_command(self) -> EventCommand:
        if not self.validate():
            raise CommandError("Angle and magnitude must be valid")
            
        angle = self.angle_input.get_value()
        magnitude = self.mag_input.get_value()
        keep_facing = self.keep_facing.isChecked()
        
        return EventCommand.vector_move(angle, magnitude, keep_facing)

    def apply_arguments(self, command: int, args: list):
        if len(args) < 2:
            return
            
        # Convert command byte angle (0-255) to degrees (0-359)
        angle_deg = int(args[0] * 360 / 256)
        self.angle_input.set_value(angle_deg)
        self.mag_input.set_value(args[1])
        
        # Command 0x9C keeps facing, 0x92 changes it
        self.keep_facing.setChecked(command == 0x9C)

class PartyFollowMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("Makes PC2 and PC3 follow PC1")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(label)
        result.setLayout(layout)
        return result
        
    def validate(self) -> bool:
        return True  # Always valid, no parameters

    def get_command(self) -> EventCommand:
        return EventCommand.party_follow()

    def apply_arguments(self, command: int, args: list):
        pass  # No arguments to apply

class MoveSpriteMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        coord_layout = QGridLayout()
        
        x_label = QLabel("X Coordinate:")
        y_label = QLabel("Y Coordinate:")
        self.x_coord = ValidatingLineEdit(min_value=0, max_value=0xFF)
        self.y_coord = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        coord_layout.addWidget(x_label, 0, 0)
        coord_layout.addWidget(self.x_coord, 0, 1)
        coord_layout.addWidget(y_label, 1, 0)
        coord_layout.addWidget(self.y_coord, 1, 1)
        
        self.animated = QCheckBox("Animated Movement")
        
        layout.addLayout(coord_layout)
        layout.addWidget(self.animated)
        result.setLayout(layout)
        return result

    def validate(self) -> bool:
        return (self.x_coord.get_value() is not None and 
                self.y_coord.get_value() is not None)

    def get_command(self) -> EventCommand:
        if not self.validate():
            raise CommandError("Coordinates must be valid")
        
        return EventCommand.move_sprite(
            self.x_coord.get_value(),
            self.y_coord.get_value(),
            self.animated.isChecked()
        )

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 2:
            self.x_coord.set_value(args[0])
            self.y_coord.set_value(args[1])
            self.animated.setChecked(command in [0xA0, 0xA1])

class MoveSpriteFromMemMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        addr_layout = QGridLayout()
        
        x_label = QLabel("X Coordinate Address:")
        y_label = QLabel("Y Coordinate Address:")
        self.x_addr = ValidatingLineEdit(min_value=0x7F0200, max_value=0x7F0400)
        self.y_addr = ValidatingLineEdit(min_value=0x7F0200, max_value=0x7F0400)
        
        x_help = QLabel("(must be in 7F0200-7F0400)")
        y_help = QLabel("(must be in 7F0200-7F0400)")
        x_help.setStyleSheet("color: gray;")
        y_help.setStyleSheet("color: gray;")
        
        addr_layout.addWidget(x_label, 0, 0)
        addr_layout.addWidget(self.x_addr, 0, 1)
        addr_layout.addWidget(x_help, 1, 0, 1, 2)
        addr_layout.addWidget(y_label, 2, 0)
        addr_layout.addWidget(self.y_addr, 2, 1)
        addr_layout.addWidget(y_help, 3, 0, 1, 2)
        
        self.animated = QCheckBox("Animated Movement")
        
        layout.addLayout(addr_layout)
        layout.addWidget(self.animated)
        result.setLayout(layout)
        return result

    def validate(self) -> bool:
        return (self.x_addr.get_value() is not None and 
                self.y_addr.get_value() is not None)

    def get_command(self) -> EventCommand:
        if not self.validate():
            raise CommandError("Addresses must be valid script memory addresses")
        
        return EventCommand.move_sprite_from_mem(
            self.x_addr.get_value(),
            self.y_addr.get_value(),
            self.animated.isChecked()
        )

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 2:
            # Convert offsets back to full addresses
            self.x_addr.set_value(0x7F0200 + args[0] * 2)
            self.y_addr.set_value(0x7F0200 + args[1] * 2)
            self.animated.setChecked(command in [0xA1])

class MoveTowardCoordMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QGridLayout()
        
        x_label = QLabel("X Coordinate:")
        y_label = QLabel("Y Coordinate:")
        dist_label = QLabel("Distance:")
        
        self.x_coord = ValidatingLineEdit(min_value=0, max_value=0xFF)
        self.y_coord = ValidatingLineEdit(min_value=0, max_value=0xFF)
        self.distance = ValidatingLineEdit(min_value=0, max_value=0xFF)
        
        layout.addWidget(x_label, 0, 0)
        layout.addWidget(self.x_coord, 0, 1)
        layout.addWidget(y_label, 1, 0)
        layout.addWidget(self.y_coord, 1, 1)
        layout.addWidget(dist_label, 2, 0)
        layout.addWidget(self.distance, 2, 1)
        
        result.setLayout(layout)
        return result

    def validate(self) -> bool:
        return (self.x_coord.get_value() is not None and 
                self.y_coord.get_value() is not None and
                self.distance.get_value() is not None)

    def get_command(self) -> EventCommand:
        if not self.validate():
            raise CommandError("All values must be valid (00-FF)")
        
        return EventCommand.move_toward_coord(
            self.x_coord.get_value(),
            self.y_coord.get_value(),
            self.distance.get_value()
        )

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 3:
            self.x_coord.set_value(args[0])
            self.y_coord.set_value(args[1])
            self.distance.set_value(args[2])

class ObjectMovementPropertiesMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        self.through_walls = QCheckBox("Through Walls")
        self.through_pcs = QCheckBox("Through PCs")
        
        layout.addWidget(self.through_walls)
        layout.addWidget(self.through_pcs)
        
        result.setLayout(layout)
        return result

    def validate(self) -> bool:
        return True  # Always valid since checkboxes can't be invalid

    def get_command(self) -> EventCommand:
        return EventCommand.set_movement_properties(
            self.through_walls.isChecked(),
            self.through_pcs.isChecked()
        )

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 1:
            self.through_walls.setChecked(args[0] & 0x01)
            self.through_pcs.setChecked(args[0] & 0x02)

class DestinationPropertiesMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        self.onto_tile = QCheckBox("Onto Tile")
        self.onto_object = QCheckBox("Onto Object")
        
        layout.addWidget(self.onto_tile)
        layout.addWidget(self.onto_object)
        
        result.setLayout(layout)
        return result

    def validate(self) -> bool:
        return True  # Always valid since checkboxes can't be invalid

    def get_command(self) -> EventCommand:
        return EventCommand.set_destination_properties(
            self.onto_tile.isChecked(),
            self.onto_object.isChecked()
        )

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 1:
            self.onto_tile.setChecked(args[0] & 0x01)
            self.onto_object.setChecked(args[0] & 0x02)

class MoveTowardTargetMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        # Target type selector
        type_layout = QHBoxLayout()
        type_label = QLabel("Target Type:")
        self.target_type = QComboBox()
        self.target_type.addItem("Object")
        self.target_type.addItem("PC")
        self.target_type.currentIndexChanged.connect(self._update_validator)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.target_type)
        
        # Target ID input
        target_layout = QHBoxLayout()
        target_label = QLabel("Target ID:")
        self.target_id = ValidatingLineEdit(min_value=0, max_value=0xFF)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_id)
        
        # Distance input
        dist_layout = QHBoxLayout()
        dist_label = QLabel("Distance:")
        self.distance = ValidatingLineEdit(min_value=0, max_value=0xFF)
        dist_layout.addWidget(dist_label)
        dist_layout.addWidget(self.distance)
        
        # Keep facing checkbox
        self.keep_facing = QCheckBox("Keep Current Facing")
        
        layout.addLayout(type_layout)
        layout.addLayout(target_layout)
        layout.addLayout(dist_layout)
        layout.addWidget(self.keep_facing)
        
        result.setLayout(layout)
        self._update_validator(0)  # Initialize for Object
        return result
        
    def _update_validator(self, index):
        """Update target ID validator based on type"""
        if index == 0:  # Object
            self.target_id.setValidator(ValidatingLineEdit(min_value=0, max_value=0xFF))
        else:  # PC
            self.target_id.setValidator(ValidatingLineEdit(min_value=1, max_value=6))

    def validate(self) -> bool:
        if self.target_id.get_value() is None:
            return False
        if self.distance.get_value() is None:
            return False
            
        if self.target_type.currentText() == "PC":
            return 1 <= self.target_id.get_value() <= 6
        else:
            return 0 <= self.target_id.get_value() <= 0xFF

    def get_command(self) -> EventCommand:
        if not self.validate():
            raise CommandError("Invalid target ID or distance")
            
        return EventCommand.move_toward_object(
            self.target_id.get_value(),
            self.distance.get_value(),
            self.target_type.currentText() == "PC",
            self.keep_facing.isChecked()
        )

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 2:
            is_pc = command in [0x99, 0x9F]
            self.target_type.setCurrentText("PC" if is_pc else "Object")
            self.target_id.set_value(args[0])
            self.distance.set_value(args[1])
            self.keep_facing.setChecked(command in [0x9E, 0x9F])

class FollowTargetMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        # Follow type selector
        type_layout = QHBoxLayout()
        type_label = QLabel("Follow Mode:")
        self.follow_type = QComboBox()
        self.follow_type.addItem("At Distance (PC only)")
        self.follow_type.addItem("Follow Object")
        self.follow_type.addItem("Follow PC")
        self.follow_type.currentIndexChanged.connect(self._update_ui)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.follow_type)
        
        # Target ID input
        target_layout = QHBoxLayout()
        target_label = QLabel("Target ID:")
        self.target_id = ValidatingLineEdit(min_value=1, max_value=6)  # Starts as PC mode
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_id)
        
        # Repeat checkbox (not shown for distance follow)
        self.repeat = QCheckBox("Repeat Follow")
        
        layout.addLayout(type_layout)
        layout.addLayout(target_layout)
        layout.addWidget(self.repeat)
        
        result.setLayout(layout)
        self._update_ui(0)  # Initialize for distance follow
        return result
        
    def _update_ui(self, index):
        """Update UI based on follow type"""
        if index == 0:  # At Distance
            self.target_id.setValidator(ValidatingLineEdit(min_value=1, max_value=6))
            self.repeat.setVisible(False)
        elif index == 1:  # Follow Object
            self.target_id.setValidator(ValidatingLineEdit(min_value=0, max_value=0xFF))
            self.repeat.setVisible(True)
        else:  # Follow PC
            self.target_id.setValidator(ValidatingLineEdit(min_value=1, max_value=6))
            self.repeat.setVisible(True)

    def validate(self) -> bool:
        if self.target_id.get_value() is None:
            return False
            
        follow_type = self.follow_type.currentIndex()
        if follow_type in [0, 2]:  # PC modes
            return 1 <= self.target_id.get_value() <= 6
        else:  # Object mode
            return 0 <= self.target_id.get_value() <= 0xFF

    def get_command(self) -> EventCommand:
        if not self.validate():
            raise CommandError("Invalid target ID")
            
        follow_type = self.follow_type.currentIndex()
        if follow_type == 0:  # At Distance
            return EventCommand.follow_pc_at_distance(self.target_id.get_value())
        else:
            return EventCommand.follow_target(
                self.target_id.get_value(),
                follow_type == 2,  # is_pc
                self.repeat.isChecked()
            )

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 1:
            if command == 0x8F:
                self.follow_type.setCurrentIndex(0)  # At Distance
                self.target_id.set_value(args[0])
            elif command in [0x94, 0xB5]:  # Follow Object
                self.follow_type.setCurrentIndex(1)
                self.target_id.set_value(args[0])
                self.repeat.setChecked(command == 0xB5)
            elif command in [0x95, 0xB6]:  # Follow PC
                self.follow_type.setCurrentIndex(2)
                self.target_id.set_value(args[0])
                self.repeat.setChecked(command == 0xB6)

class SetSpeedMenu(BaseCommandMenu):
    def command_widget(self) -> QWidget:
        result = QWidget()
        layout = QVBoxLayout()
        
        # Speed type selector
        type_layout = QHBoxLayout()
        type_label = QLabel("Speed Source:")
        self.speed_type = QComboBox()
        self.speed_type.addItem("Direct Value")
        self.speed_type.addItem("From Memory")
        self.speed_type.currentIndexChanged.connect(self._update_ui)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.speed_type)
        
        # Speed value input
        value_layout = QHBoxLayout()
        self.value_label = QLabel("Speed Value:")
        self.speed_value = ValidatingLineEdit(min_value=0, max_value=0xFF)
        value_layout.addWidget(self.value_label)
        value_layout.addWidget(self.speed_value)
        
        # Memory address input
        addr_layout = QHBoxLayout()
        self.addr_label = QLabel("Memory Address:")
        self.speed_addr = ValidatingLineEdit(min_value=0x7F0200, max_value=0x7F0400)
        addr_layout.addWidget(self.addr_label)
        addr_layout.addWidget(self.speed_addr)
        
        layout.addLayout(type_layout)
        layout.addLayout(value_layout)
        layout.addLayout(addr_layout)
        
        result.setLayout(layout)
        self._update_ui(0)  # Initialize for direct value
        return result
        
    def _update_ui(self, index):
        """Update UI based on speed source"""
        is_direct = index == 0
        self.value_label.setVisible(is_direct)
        self.speed_value.setVisible(is_direct)
        self.addr_label.setVisible(not is_direct)
        self.speed_addr.setVisible(not is_direct)

    def validate(self) -> bool:
        if self.speed_type.currentIndex() == 0:
            return self.speed_value.get_value() is not None
        else:
            return self.speed_addr.get_value() is not None

    def get_command(self) -> EventCommand:
        if not self.validate():
            raise CommandError("Invalid speed value or address")
            
        if self.speed_type.currentIndex() == 0:
            return EventCommand.set_speed(self.speed_value.get_value())
        else:
            return EventCommand.set_speed_from_mem(self.speed_addr.get_value())

    def apply_arguments(self, command: int, args: list):
        if len(args) >= 1:
            if command == 0x89:
                self.speed_type.setCurrentIndex(0)
                self.speed_value.set_value(args[0])
            else:  # 0x8A
                self.speed_type.setCurrentIndex(1)
                self.speed_addr.set_value(0x7F0200 + args[0] * 2)

menu_mapping = {
    EventCommandType.UNASSIGNED: {
        EventCommandSubtype.UNASSIGNED: UnassignedMenu()
    },
    EventCommandType.ANIMATION: {
        EventCommandSubtype.ANIMATION: AnimationMenu(),
        EventCommandSubtype.ANIMATION_LIMITER: AnimationLimiterMenu(),
        EventCommandSubtype.RESET_ANIMATION: ResetAnimationMenu()
    },
    EventCommandType.ASSIGNMENT: {
        EventCommandSubtype.GET_PC1: GetPC1Menu(),
        EventCommandSubtype.GET_STORYLINE: GetStoryCtrMenu(),
        EventCommandSubtype.MEM_TO_MEM_ASSIGN: MemToMemAssignMenu(),
        EventCommandSubtype.RESULT: ResultMenu(),
        EventCommandSubtype.SET_STORYLINE: SetStorylineMenu(),
        EventCommandSubtype.VAL_TO_MEM_ASSIGN: ValToMemAssignMenu(),
    },  
    EventCommandType.BATTLE: {
        EventCommandSubtype.BATTLE: BattleMenu()
    },
    EventCommandType.BIT_MATH: {},
    EventCommandType.BYTE_MATH: {},
    EventCommandType.CHANGE_LOCATION: {},
    EventCommandType.CHECK_BUTTON: {
        EventCommandSubtype.CHECK_BUTTON: CheckButtonMenu()
    },
    EventCommandType.CHECK_PARTY: {},
    EventCommandType.CHECK_RESULT: {},
    EventCommandType.CHECK_STORYLINE: {},
    EventCommandType.COMPARISON: {},
    EventCommandType.END: {},
    EventCommandType.FACING: {},
    EventCommandType.GOTO: {},
    EventCommandType.HP_MP: {},
    EventCommandType.INVENTORY: {
        EventCommandSubtype.EQUIP: EquipItemMenu(),
        EventCommandSubtype.GET_AMOUNT: GetItemQuantityMenu(),
        EventCommandSubtype.CHECK_GOLD: CheckGoldMenu(),
        EventCommandSubtype.ADD_GOLD: AddGoldMenu(),
        EventCommandSubtype.CHECK_ITEM: ItemMenu(),
        EventCommandSubtype.ITEM: ItemMenu(),
        EventCommandSubtype.ITEM_FROM_MEM: ItemFromMemMenu()
    },
    EventCommandType.MEM_COPY: {},
    EventCommandType.MODE7: {},
    EventCommandType.OBJECT_COORDINATES: {},
    EventCommandType.OBJECT_FUNCTION: {},
    EventCommandType.PALETTE: {
        EventCommandSubtype.CHANGE_PALETTE: ChangePaletteMenu()
    },
    EventCommandType.PAUSE: {},
    EventCommandType.PARTY_MANAGEMENT: {},
    EventCommandType.RANDOM_NUM: {
        EventCommandSubtype.RANDOM_NUM: RandomNumberMenu()
    },
    EventCommandType.SCENE_MANIP: {
        EventCommandSubtype.SCRIPT_SPEED: ScriptSpeedMenu()
    },
    EventCommandType.SOUND: {},
    EventCommandType.SPRITE_COLLISION: {
        EventCommandSubtype.SPRITE_COLLISION: SpriteCollisionMenu()
    },
    EventCommandType.SPRITE_DRAWING: {},
    EventCommandType.SPRITE_MOVEMENT: {
        EventCommandSubtype.CONTROLLABLE: ControllableMenu(),
        EventCommandSubtype.EXPLORE_MODE: ExploreModeMenu(),
        # Jump
        # Jump 7B
        EventCommandSubtype.MOVE_PARTY: MovePartyMenu(),
        EventCommandSubtype.MOVE_SPRITE: MoveSpriteMenu(),
        EventCommandSubtype.MOVE_SPRITE_FROM_MEM: MoveSpriteFromMemMenu(),
        EventCommandSubtype.MOVE_TOWARD_COORD: MoveTowardCoordMenu(),
        EventCommandSubtype.MOVE_TOWARD_OBJ: MoveTowardTargetMenu(),
        EventCommandSubtype.OBJECT_FOLLOW: FollowTargetMenu(),
        EventCommandSubtype.OBJECT_MOVEMENT_PROPERTIES: ObjectMovementPropertiesMenu(),
        EventCommandSubtype.PARTY_FOLLOW: PartyFollowMenu(),
        EventCommandSubtype.DESTINATION: DestinationPropertiesMenu(),
        EventCommandSubtype.VECTOR_MOVE: VectorMoveMenu(),
        #EventCommandSubtype.VECTOR_MOVE_FROM_MEM: 
        EventCommandSubtype.SET_SPEED: SetSpeedMenu(),
        # EventCommandSubtype.SET_SPEED_FROM_MEM: 
    },
    EventCommandType.TEXT: {
        EventCommandSubtype.LOAD_ASCII: LoadASCIIMenu(),
        EventCommandSubtype.SPECIAL_DIALOG: SpecialDialogMenu(),
        EventCommandSubtype.STRING_INDEX: StringIndexMenu(),
        EventCommandSubtype.TEXTBOX: TextboxMenu()
    },
}