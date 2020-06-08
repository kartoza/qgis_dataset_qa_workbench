import typing
from pathlib import Path

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
import qgis.gui

from . import models
from .checklist_picker import ChecklistPicker
from .utils import log_message

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
UI_DIR = Path(__file__).parents[1] / "ui"
FORM_CLASS, _ = uic.loadUiType(
    str(UI_DIR / 'checklist_checker_dock_base.ui'))


class ChecklistCheckerDock(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = QtCore.pyqtSignal()

    def __init__(self, checklists: typing.List[models.Checklist], parent=None):
        """Constructor."""
        super(ChecklistCheckerDock, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.checklists = checklists
        self.choose_checklist_pb.clicked.connect(self.show_checklist_picker)

    def show_checklist_picker(self):
        self.checklist_picker_dlg = ChecklistPicker(self.checklists)
        self.checklist_picker_dlg.show()
        result = self.checklist_picker_dlg.exec_()
        if result:
            log_message('checklist picker has a result')
            try:
                selected_idx = self.checklist_picker_dlg.checklists_tv.selectedIndexes()[0]
                selected_checklist = self.checklists[selected_idx.row()]
                log_message(f'the selected checklist is: {selected_checklist.name}')
            except IndexError:
                pass



    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.closingPlugin.emit()
        event.accept()
