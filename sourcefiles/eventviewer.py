'''
Chrono Trigger Event Viewer
'''
from __future__ import annotations
from typing import ByteString

import commandtotext as c2t
import cli.arguments as arguments
import location_data as location_data
from eventcommand import EventCommand
from commandgroups import event_command_groupings
import commandmenus as cm
from commanditemmodel import CommandModel, CommandItem

import ctevent
from PyQt6.QtWidgets import QApplication, QMainWindow, QTreeView, QTreeWidgetItem, QVBoxLayout, QWidget, QComboBox, QPushButton, QLabel, QGridLayout
from PyQt6.QtCore import Qt
import sys

def process_script(script):
        result = []
        for i in range(script.num_objects):
            object = CommandItem(f"Object {i:02X}")
            all_functions = script.get_all_fuctions(i)
            num = 0
            for f in all_functions:
                func_start = script.get_function_start(i, num)
                if num > 2 and script.get_function_start(i, num) == script.get_function_start(i, num-1):
                    break
                func_name = "Startup"
                if num == 1:
                    func_name = "Activate"
                if num == 2:
                    func_name = "Touch"
                if num > 2:
                    func_id = num - 3
                    func_name = f"Function {func_id:02X}"
                func = CommandItem(func_name)
                num += 1
                (children, _) = create_command_list(f.commands, func_start)
                func.add_children(children)
                object.add_child(func)
            result.append(object)
        return result

def create_command_list(commands, bytes=0):
    items = []
    i = 0
    curr_bytes = bytes
    while i < len(commands):
        command_str = c2t.command_to_text(commands[i], curr_bytes)
        command_bytes = len(commands[i])
        item = CommandItem(command_str, commands[i], "0x{:02X}".format(curr_bytes))
        if commands[i].command in EventCommand.conditional_commands:
            bytes_to_jump = commands[i].args[commands[i].num_args-1]
            if bytes_to_jump <= 0: 
                i+=1
                continue
            start = i+1
            while bytes_to_jump > 0:
                i+=1
                if i >= len(commands):
                    break
                bytes_to_jump -= len(commands[i])
            end = i
            (child_items, skipped_bytes) = create_command_list(commands[start:end], curr_bytes+command_bytes)
            item.add_children(child_items)
            curr_bytes += skipped_bytes
            i-=1
        items.append(item)
        curr_bytes += command_bytes
        i+=1

    return (items, curr_bytes-bytes)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        parser = arguments.get_parser()
        args = parser.parse_args()

        if not args.input_file.exists():
            raise FileNotFoundError("Invalid input file path.")

        self.rom = args.input_file.read_bytes()
        self.current_command = None
        self.curr_address = None
        self.main_layout = QGridLayout()
        
        self.setWindowTitle("Chrono Trigger Event Editor")
        self.script = ctevent.Event.from_rom_location(self.rom, location_data.locations[0][0])
        root = CommandItem("Root")
        children = process_script(self.script)
        root.add_children(children)
        self.model = CommandModel(root)
        self.model.dataChanged.connect(self.on_data_changed)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        
        self.tree.setMinimumHeight(750)
        self.tree.setMinimumWidth(750)
        self.tree.setColumnWidth(0, 70)
        #self.tree.header().setVisible(False)
        self.tree.setTreePosition(1)

        

        widget = QWidget()
        self.command_layout = QVBoxLayout()
        command_widget = QWidget()

        self.location_selector = QComboBox()
        i = 0
        for (id, name) in location_data.locations:
            self.location_selector.addItem(name)
            self.location_selector.setItemData(i, id)
            i+=1
        self.location_selector.currentIndexChanged.connect(self.on_location_box_changed)

        self.command_group_selector = QComboBox()
        self.command_subgroup_selector = None
        i = 0
        for key in event_command_groupings:
            self.command_group_selector.addItem(key.value)
            subgroups = QComboBox()
            for subkey in event_command_groupings[key]:
                subgroups.addItem(subkey.value)
            self.command_group_selector.setItemData(i, subgroups)
            if self.command_subgroup_selector is None:
                self.command_subgroup_selector = subgroups
            i +=1
        
        self.tree.selectionModel().selectionChanged.connect(self.on_item_changed)
        

        self.update_button = QPushButton(text="Update")
        self.update_button.clicked.connect(self.on_update_pressed)

        self.current_command_label = QLabel()
        self.current_command_label.text = ""

        self.main_layout.addWidget(self.location_selector, 0, 0, 1, 2)
        self.main_layout.addWidget(self.tree, 1, 1)
        #self.layout.addWidget(self.button)
        self.main_layout.addWidget(self.current_command_label, 2, 0, 1, 2)
        self.mem_to_mem_menu = cm.MemToMemMenu()
        self.command_layout.addWidget(self.command_group_selector)
        self.command_layout.addWidget(self.command_subgroup_selector)
        self.command_layout.addWidget(self.mem_to_mem_menu.command_widget())
        self.command_layout.addWidget(self.update_button)
        command_widget.setLayout(self.command_layout)
        self.main_layout.addWidget(command_widget, 1, 0, 1, 1, Qt.AlignmentFlag.AlignTop)
        #self.main_layout.addWidget(self.command_group_selector, 1, 0, 1, 1, Qt.AlignmentFlag.AlignTop)
        #self.main_layout.addWidget(self.command_subgroup_selector, 2, 0, 1, 1, Qt.AlignmentFlag.AlignTop)
        self.main_layout.setColumnStretch(0, 0)
        self.main_layout.setColumnStretch(1, 2)
        self.main_layout.setColumnMinimumWidth(1, 300)
        widget.setLayout(self.main_layout)
        self.setCentralWidget(widget)
        # expand_tree(self.tree)
        self.tree.expandAll()

    def on_item_changed(self, selected, deselected):
        # Get the currently selected index
        indexes = selected.indexes()
        
        if indexes:
            # Take first selected index (from first column)
            index = indexes[0]
            item: CommandItem = index.internalPointer()
            if item.command:
                text = str(item.command)
                text += "\n" + str(item.command.desc)
                text += "\n" + str(item.command.args)
                text += "\n" + str(item.command.arg_descs)
                self.current_command_label.setText(text)
                if item.command.command_type is not None:
                    i = self.command_group_selector.findText(item.command.command_type.value)
                    if i == -1:
                        return
                    self.command_group_selector.setCurrentIndex(i)
                    self.command_subgroup_selector.clear()
                    for subkey in event_command_groupings[item.command.command_type]:
                        self.command_subgroup_selector.addItem(subkey.value)


                    i = self.command_subgroup_selector.findText(item.command.command_subtype.value)
                    if i != -1:
                        self.command_subgroup_selector.setCurrentIndex(i)

    def on_update_pressed(self):
        new_comm = self.mem_to_mem_menu.get_command()
        print(new_comm)
        room = self.location_selector.currentData()
        print(room)
        # script = ctevent.Event.from_rom_location(self.rom, self.location_selector.currentData())
        from_cmd = self.tree.currentIndex().internalPointer()
        print(from_cmd.command)
        self.script.replace_command(from_cmd.command, new_comm, self.curr_address)
        self.model.update_command(from_cmd, new_comm)
        self.tree.viewport().update()
        #self.tree.clear()
        #self.script = ctevent.Event.from_rom_location(self.rom, selected_value)
        #self.tree.insertTopLevelItems(0, create_command_view(self.script))
        #print(str(self.script.get_function(0,0)))
        

    def on_location_box_changed(self, index):
        selected_value = self.location_selector.itemData(index)
        print(f"Selected value: {selected_value}")
        self.script = ctevent.Event.from_rom_location(self.rom, selected_value)
        new_root = CommandItem(name="Root", children=process_script(self.script))
        self.model.replace_items(new_root)
        # expand_tree(self.tree)
        self.tree.expandAll()


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()

# def main():



# if __name__ == "__main__":
#     main()
