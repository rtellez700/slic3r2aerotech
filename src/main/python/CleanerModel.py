from Slic3rCleaner import Slic3rCleaner
from itertools import count
from PyQt5 import uic


class ToolModel(object):
    """
    This class is model-viewer mashup. It holds the tool information and also
    updates the Qdialog.
    """
    def __init__(self,tool_number, cleaner_model,tool_dlg_resource):
        self.dlg = uic.loadUi(tool_dlg_resource)
        self.tool_number = tool_number
        self.pressure = 0
        self.comport = 0
        self.xoffset = 0.0
        self.yoffset = 0.0
        self.velocity = False
        self.aeroaxis = 'Z'
        self.cleaner_model = cleaner_model
        self.setup_connects()
        self.refreshAll()


    def refreshAll( self ):
        """
        update all of the text fields with the stored info for the tool
        """
        self.dlg.slicer_tool_line.insert(str(self.tool_number))
        self.dlg.comport_line.insert(str(self.comport))
        self.dlg.pressure_line.insert(str(self.pressure))
        self.dlg.offset_y_line.insert(str(self.yoffset))
        self.dlg.offset_x_line.insert(str(self.xoffset))
        #self.dlg.slicer_tool_line.update()
        self.dlg.update()

    def update_tool_number(self):
        self.cleaner_model.tools[int(self.dlg.slicer_tool_line.text())] = self.cleaner_model.tools.pop(self.tool_number)
        self.tool_number = int(self.dlg.slicer_tool_line.text())
        #self.cleaner_model.parent_window.update_view()

    def update_model(self):
        self.pressure = float(self.dlg.pressure_line.text())
        self.comport = int(self.dlg.comport_line.text())
        self.xoffset = float(self.dlg.offset_x_line.text())
        self.yoffset = float(self.dlg.offset_y_line.text())
        self.aeroaxis = self.dlg.aerotech_line.text()
        self.velocity = self.dlg.velocity_checkbox.isChecked()

    def setup_connects(self):
        self.dlg.slicer_tool_line.editingFinished.connect(self.update_tool_number)
        self.dlg.pressure_line.editingFinished.connect(self.update_model)
        self.dlg.comport_line.editingFinished.connect(self.update_model)
        self.dlg.offset_x_line.editingFinished.connect(self.update_model)
        self.dlg.offset_y_line.editingFinished.connect(self.update_model)
        self.dlg.aerotech_line.editingFinished.connect(self.update_model)
        self.dlg.velocity_checkbox.toggled.connect(self.update_model)


class CleanerModel:
    def __init__(self,parent_window,tool_dlg_resource):
        self.tools = {}
        self.num_tools = 0
        self.active_tool = None
        self.CleanerWindow = parent_window
        self.infile = None
        self.outfile = None
        self.tool_dlg_resource = tool_dlg_resource

    def isValid( self, fileName ):
        '''
        returns True if the file exists and can be
        opened.  Returns False otherwise.
        '''
        try:
            file = open( fileName, 'r' )
            file.close()
            return True
        except:
            return False

    def _first_missing_sequence(self,sequence, start=0):
        uniques = set(sequence) # { x for x in sequence if x>=start }
        return next( x for x in count(start) if x not in uniques )

    def add_tool(self):
        self.num_tools += 1
        newtool_number = self._first_missing_sequence(list(self.tools.keys()))
        self.tools[newtool_number] = ToolModel(newtool_number,self,self.tool_dlg_resource)
        self.active_tool = self.tools[newtool_number]
        return self.tools[newtool_number]


    def remove_tool(self,active_tool_number):
        if (self.num_tools is not None) and (self.num_tools > 0):
            self.num_tools -= 1
            self.tools.pop(self.active_tool.tool_number)
            self.active_tool = None

    def set_active_tool(self, active_tool_number):
        print(self.tools.keys())
        self.active_tool = self.tools[int(active_tool_number)]
