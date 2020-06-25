import json
import typing
from pathlib import Path

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from . import models
from . import utils
from .checklist_downloader import ChecklistDownloader
from .constants import (
    ChecklistModelColumn,
    CustomDataRoles,
)

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
UI_DIR = Path(__file__).parents[1] / "ui"
FORM_CLASS, _ = uic.loadUiType(
    str(UI_DIR / 'checklist_picker.ui'))


class ChecklistPicker(QtWidgets.QDialog, FORM_CLASS):
    button_box: QtWidgets.QDialogButtonBox
    checklist_downloader_dlg: ChecklistDownloader
    checklist_save_path_la: QtWidgets.QLabel
    checklists_tv: QtWidgets.QTreeView
    delete_checklist_pb: QtWidgets.QPushButton
    download_checklist_pb: QtWidgets.QPushButton

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(ChecklistPicker, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.download_checklist_pb.clicked.connect(self.show_checklist_downloader)
        self.delete_checklist_pb.setEnabled(False)
        self.delete_checklist_pb.clicked.connect(self.delete_checklist)
        self.checklist_save_path_la.setText(f'Checklists are loaded from {utils.get_checklists_dir()}')
        checklists = models.load_checklists()
        self.model = QtGui.QStandardItemModel(len(checklists), 3)
        self.model.setHorizontalHeaderLabels([i.name.replace('_', ' ').capitalize() for i in ChecklistModelColumn])
        self.checklists_tv.setModel(self.model)
        self.checklists_tv.selectionModel().selectionChanged.connect(self.enable_checklist_actions)
        self.model.rowsRemoved.connect(self.toggle_delete_checklist_button)
        self.button_box.button(self.button_box.Ok).setEnabled(False)
        self.load_checklists(checklists)

    def enable_checklist_actions(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        button = self.button_box.button(self.button_box.Ok)
        button.setEnabled(bool(len(selected.indexes())))
        self.delete_checklist_pb.setEnabled(bool(len(selected.indexes())))

    def toggle_delete_checklist_button(self, parent: QtCore.QModelIndex, first: int, last: int):
        self.delete_checklist_pb.setEnabled(self.model.rowCount() != 0)

    def delete_checklist(self):
        idx = self.checklists_tv.currentIndex()
        if idx.isValid():
            model = self.checklists_tv.model()
            identifier_index = model.index(idx.row(), 0)
            checklist = identifier_index.data(role=CustomDataRoles.CHECKLIST_DOWNLOADER_IDENTIFIER.value)
            path = utils.get_checklists_dir() / f'{sanitize_checklist_name(checklist.name)}.json'
            try:
                path.unlink()
            except FileNotFoundError as exc:
                utils.log_message(str(exc))
            else:
                model.removeRow(idx.row())

    def load_checklists(self, checklists: typing.List[models.CheckList]):
        self.checklists_tv.selectionModel().select(QtCore.QItemSelection(), QtCore.QItemSelectionModel.Clear)
        self.model.clear()
        self.model.setHorizontalHeaderLabels([i.name.replace('_', ' ').capitalize() for i in ChecklistModelColumn])
        for row_index, checklist in enumerate(checklists):
            checklist: models.CheckList
            identifier_item = QtGui.QStandardItem(str(checklist.identifier))
            identifier_item.setData(checklist, role=CustomDataRoles.CHECKLIST_DOWNLOADER_IDENTIFIER.value)
            self.model.setItem(row_index, ChecklistModelColumn.IDENTIFIER.value, identifier_item)
            self.model.setItem(
                row_index, ChecklistModelColumn.NAME.value, QtGui.QStandardItem(checklist.name))
            self.model.setItem(
                row_index,
                ChecklistModelColumn.DATASET_TYPE.value,
                QtGui.QStandardItem(checklist.dataset_type.value)
            )
            self.model.setItem(
                row_index,
                ChecklistModelColumn.APPLICABLE_TO.value,
                QtGui.QStandardItem(checklist.validation_artifact_type.value)
            )
        # self.checklists_tv.setModel(self.model)
        self.checklists_tv.setColumnHidden(ChecklistModelColumn.IDENTIFIER.value, True)
        header = self.checklists_tv.header()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

        # self.checklists_tv.setSortingEnabled(True)
        # self.checklists_tv.sortByColumn(ChecklistModelColumn.DATASET_TYPES.value, QtCore.Qt.DescendingOrder)

    def show_checklist_downloader(self):
        self.checklist_downloader_dlg = ChecklistDownloader(self.iface)
        self.checklist_downloader_dlg.button_box.accepted.connect(self.load_checklist)
        self.checklist_downloader_dlg.setModal(True)
        self.checklist_downloader_dlg.show()
        self.checklist_downloader_dlg.exec_()
        # self.delete_checklist_pb.setEnabled(False)

    def load_checklist(self):
        utils.log_message(f'load_checklist called')
        selected_checklist_indexes = self.checklist_downloader_dlg.downloaded_checklists_tv.selectedIndexes()
        for idx in selected_checklist_indexes:
            model = idx.model()
            idx: QtCore.QModelIndex
            identifier_idx = model.index(idx.row(), 0, idx.parent())
            checklist = identifier_idx.data(CustomDataRoles.CHECKLIST_DOWNLOADER_IDENTIFIER.value)
            sanitized_name = sanitize_checklist_name(checklist.name)
            target_path = utils.get_checklists_dir() / f'{sanitized_name}.json'
            # TODO: Add a try block
            save_checklist(checklist, target_path)
        existing_checklists = models.load_checklists()
        self.load_checklists(existing_checklists)


def sanitize_checklist_name(name: str) -> str:
    return name.replace(' ', '_').lower()


def save_checklist(checklist: models.CheckList, target_path: Path):
    serialized = json.dumps(
        checklist.to_dict(
            include_check_notes=False,
            include_check_results=False,
            include_check_automation=True
        ),
        indent=2
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    # TODO: Use QGIS native encoding
    target_path.write_text(serialized, encoding='utf-8')
    utils.log_message(f'saving checklist {serialized}...')
