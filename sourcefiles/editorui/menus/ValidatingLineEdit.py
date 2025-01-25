from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLineEdit


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