import typing
from enum import Enum
from pathlib import Path

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from . import models
from . import utils
from .constants import ChecklistModelColumn

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
UI_DIR = Path(__file__).parents[1] / "ui"
FORM_CLASS, _ = uic.loadUiType(
    str(UI_DIR / 'checklist_picker.ui'))


class ChecklistPicker(QtWidgets.QDialog, FORM_CLASS):
    checklist_save_path_la: QtWidgets.QLabel

    def __init__(self, checklists: typing.List[models.NewCheckList], parent=None):
    # def __init__(self, checklists: typing.List[models.Checklist], parent=None):
        """Constructor."""
        super(ChecklistPicker, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.checklist_save_path_la.setText(f'Checklists are loaded from {utils.get_checklists_dir()}')
        self.checklists = checklists
        self.model = QtGui.QStandardItemModel(len(checklists), 3)
        self.model.setHorizontalHeaderLabels([i.name.replace('_', ' ').capitalize() for i in ChecklistModelColumn])
        for row_index, checklist in enumerate(checklists):
            checklist: models.Checklist
            self.model.setItem(
                row_index, ChecklistModelColumn.IDENTIFIER.value, QtGui.QStandardItem(str(checklist.identifier))
            )
            self.model.setItem(
                row_index, ChecklistModelColumn.NAME.value, QtGui.QStandardItem(checklist.name))
            self.model.setItem(
                row_index, ChecklistModelColumn.DESCRIPTION.value, QtGui.QStandardItem(checklist.description))
            self.model.setItem(
                row_index,
                ChecklistModelColumn.DATASET_TYPES.value,
                QtGui.QStandardItem(checklist.dataset_type.value)
            )
            self.model.setItem(
                row_index,
                ChecklistModelColumn.APPLICABLE_TO.value,
                QtGui.QStandardItem(checklist.validation_artifact_type.value)
            )
        self.checklists_tv: QtWidgets.QTreeView
        self.checklists_tv.setModel(self.model)
        self.checklists_tv.setColumnHidden(ChecklistModelColumn.IDENTIFIER.value, True)
        self.checklists_tv.setSortingEnabled(True)
        self.checklists_tv.sortByColumn(ChecklistModelColumn.DATASET_TYPES.value, QtCore.Qt.DescendingOrder)
