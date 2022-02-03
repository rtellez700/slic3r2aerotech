from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5 import uic
from Slic3rCleaner import Slic3rCleaner
from CleanerModel import CleanerModel, ToolModel
from itertools import count


import sys


class CleanerProgram(object):
    def __init__(self):
        cleaner_window_resource = appctxt.get_resource('cleaner_window.ui')
        self.tool_dlg_resource = appctxt.get_resource('tool_dialog.ui')
        self.window = uic.loadUi(cleaner_window_resource)
        self.cleaner_model = CleanerModel(self,self.tool_dlg_resource)
        self.setup_connects()

    def update_view(self):
        for i in reversed(range(self.window.tool_layout.count())):
            self.window.tool_layout.itemAt(i).widget().hide()
            self.window.tool_layout.removeWidget(self.window.tool_layout.itemAt(i).widget())
        crow = self.window.tool_list_widget.currentRow()
        self.window.tool_list_widget.clear()
        self.window.tool_list_widget.addItems([str(i) for i in self.cleaner_model.tools.keys()])
        if self.cleaner_model.active_tool is not None:
            self.window.tool_layout.addWidget(self.cleaner_model.active_tool.dlg) # set to new active item
            self.cleaner_model.active_tool.dlg.show()
            self.window.tool_list_widget.setCurrentRow(crow)
        self.window.infile_path.setText(self.cleaner_model.infile)
        self.window.outfile_path.setText(self.cleaner_model.outfile)

    def add_tool(self):
        tool = self.cleaner_model.add_tool()
        self.update_view()

    def remove_tool(self):
        self.cleaner_model.remove_tool(self.window.tool_list_widget.currentItem().text())
        self.update_view()

    def update_active_tool(self):

        self.cleaner_model.set_active_tool(self.window.tool_list_widget.currentItem().text())
        #print(self.window.tool_list_widget.currentItem().text())
        self.update_view()

    def browse_infile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
                        None,
                        "QFileDialog.getOpenFileName()",
                        "",
                        "All Files (*);;Gcode Files (*.gcode)",
                        options=options)
        self.cleaner_model.infile = fileName
        self.update_view()


    def browse_outfile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(
                        None,
                        "QFileDialog.getSaveFileName()",
                        "",
                        "All Files (*);;Gcode Files (*.pgm)",
                        options=options)
        self.cleaner_model.outfile = fileName
        self.update_view()

    def update_infile(self):
        self.cleaner_model.infile = self.window.infile_path.text()

    def update_outfile(self):
        self.cleaner_model.outfile = self.window.outfile_path.text()

    def do_the_thing(self):
        assert self.cleaner_model.isValid(self.cleaner_model.infile)
        print('doing the thing')
        the_cleaner = Slic3rCleaner(self.cleaner_model.tools,
                                    self.cleaner_model.infile,
                                    self.cleaner_model.outfile)
        the_cleaner.run_lines()

    def setup_connects(self):
        self.window.tool_list_widget.clicked.connect(self.update_active_tool)
        self.window.add_tool_button.clicked.connect(self.add_tool)
        self.window.remove_tool_button.clicked.connect(self.remove_tool)
        self.window.browse_infile.clicked.connect(self.browse_infile)
        self.window.browse_outfile.clicked.connect(self.browse_outfile)
        self.window.outfile_path.editingFinished.connect(self.update_outfile)
        self.window.infile_path.editingFinished.connect(self.update_infile)
        self.window.slic3r_clean_button.clicked.connect(self.do_the_thing)

    def run_program(self):
        self.window.show()
        return appctxt.app.exec_()


if __name__ == '__main__':
    appctxt = ApplicationContext()
    prg = CleanerProgram()
    exit_code = prg.run_program()

    sys.exit(exit_code)
