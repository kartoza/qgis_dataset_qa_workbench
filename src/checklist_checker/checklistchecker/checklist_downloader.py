import json
import typing
from pathlib import Path

from qgis.core import (
    QgsNetworkAccessManager,
    QgsSettings,
)
from PyQt5 import uic
from PyQt5 import (
    QtCore,
    QtGui,
    QtNetwork,
    QtWidgets,
)

from . import models
from . import utils
from .checklist_server_editor import ChecklistEditor
from .constants import (
    ChecklistModelColumn,
    CustomDataRoles,
    SETTINGS_GROUP,
)

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
UI_DIR = Path(__file__).parents[1] / "ui"
FORM_CLASS, _ = uic.loadUiType(
    str(UI_DIR / 'checklist_downloader.ui'))


class ChecklistDownloader(QtWidgets.QDialog, FORM_CLASS):
    current_server_cb: QtWidgets.QComboBox
    connect_to_server_pb: QtWidgets.QPushButton
    new_server_pb: QtWidgets.QPushButton
    edit_server_pb: QtWidgets.QPushButton
    remove_server_pb: QtWidgets.QPushButton
    add_default_servers_pb: QtWidgets.QPushButton
    downloaded_checklists_tv: QtWidgets.QTreeView
    model: QtGui.QStandardItemModel

    def __init__(self, parent=None):
        super().__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.model = QtGui.QStandardItemModel()
        self.model.setColumnCount(3)
        self.downloaded_checklists_tv.setModel(self.model)
        self.reset_tree_view()
        self.new_server_pb.clicked.connect(self.show_new_server_dialog)
        self.load_known_servers()
        if self.current_server_cb.count() == 0:
            self.remove_server_pb.setEnabled(False)
            self.connect_to_server_pb.setEnabled(False)
            self.edit_server_pb.setEnabled(False)
        self.current_server_cb.currentIndexChanged.connect(self.toggle_server_buttons)
        self.add_default_servers_pb.clicked.connect(self.add_default_servers)
        self.connect_to_server_pb.clicked.connect(self.download_checklists)
        self.remove_server_pb.clicked.connect(self.remove_server)

    def reset_tree_view(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels([i.name.replace('_', ' ').capitalize() for i in ChecklistModelColumn])
        self.downloaded_checklists_tv.setColumnHidden(ChecklistModelColumn.IDENTIFIER.value, True)
        self.downloaded_checklists_tv.setSortingEnabled(True)

    def toggle_server_buttons(self, index: int):
        if index == -1:
            self.remove_server_pb.setEnabled(False)
            self.connect_to_server_pb.setEnabled(False)
            self.edit_server_pb.setEnabled(False)
        else:
            self.remove_server_pb.setEnabled(True)
            self.connect_to_server_pb.setEnabled(True)
            self.edit_server_pb.setEnabled(True)

    def remove_server(self):
        current_server: models.ChecklistServer = self.current_server_cb.currentData()
        utils.log_message(f'about to delete current_server: {current_server.name}')
        self.current_server_cb.removeItem(self.current_server_cb.currentIndex())
        self.reset_tree_view()
        settings = QgsSettings()
        settings.beginGroup(f'{SETTINGS_GROUP}/checklist_servers')
        settings.remove(current_server.name)

    def load_known_servers(self):
        # TODO: Retrieve these from the QGIS settings object
        settings = QgsSettings()
        settings.beginGroup('PythonPlugins/checklist_checker/checklist_servers')
        for server_name in settings.childKeys():
            checklist_server = models.ChecklistServer(server_name, settings.value(server_name))
            self.current_server_cb.addItem(checklist_server.name, userData=checklist_server)
        settings.endGroup()

    def add_default_servers(self):
        default_servers = [
            models.ChecklistServer(
                'Kartoza checklists for GeoCRIS and DomiNode',
                'https://kartoza.github.io/qgis_checklist_checker/checklists/checklists.json'
            ),
        ]
        settings = QgsSettings()
        settings.beginGroup('PythonPlugins/checklist_checker/checklist_servers')
        existing_servers = settings.childKeys()
        for default_server in default_servers:
            if default_server.name not in existing_servers:
                settings.setValue(default_server.name, default_server.url)
                self.current_server_cb.addItem(default_server.name, userData=default_server)
        settings.endGroup()

    def download_checklists(self):
        current_server: models.ChecklistServer = self.current_server_cb.currentData()
        utils.log_message(f'current_server: {current_server.name}, {current_server.url}')
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(current_server.url))
        network_access_manager = QgsNetworkAccessManager.instance()
        reply: QtNetwork.QNetworkReply = network_access_manager.get(request)
        reply.finished.connect(self.parse_response)

    def parse_response(self):
        reply: QtNetwork.QNetworkReply = self.sender()
        reply_text = bytes(reply.readAll())
        status_code = reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            try:
                raw_checklists: typing.List[typing.Dict] = json.loads(reply_text)
            except json.JSONDecodeError as exc:
                utils.log_message(f'Could not parse response: {exc}')
            else:
                parsed_checklists = []
                for raw_checklist in raw_checklists:
                    # TODO: add a try block here
                    checklist = models.NewCheckList.from_dict(raw_checklist)
                    parsed_checklists.append(checklist)
                self.populate_downloaded_checklists_tree_view(parsed_checklists)
        else:
            utils.log_message(f'Received invalid response from {reply.url().toString()}: {reply_text}')

    def populate_downloaded_checklists_tree_view(self, checklists: typing.List[models.NewCheckList]):
        # self.model.clear()
        # self.model.setHorizontalHeaderLabels([i.name.replace('_', ' ').capitalize() for i in ChecklistModelColumn])
        self.reset_tree_view()
        self.model.setRowCount(len(checklists))
        for row_index, checklist in enumerate(checklists):
            checklist: models.NewCheckList
            id_item = QtGui.QStandardItem(str(checklist.identifier))
            id_item.setData(checklist, role=CustomDataRoles.CHECKLIST_DOWNLOADER_IDENTIFIER.value)
            # self.model.setItem(
            #     row_index, ChecklistModelColumn.IDENTIFIER.value, QtGui.QStandardItem(str(checklist.identifier))
            # )
            self.model.setItem(row_index, ChecklistModelColumn.IDENTIFIER.value, id_item)
            self.model.setItem(
                row_index, ChecklistModelColumn.NAME.value, QtGui.QStandardItem(checklist.name))
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
        self.downloaded_checklists_tv.sortByColumn(ChecklistModelColumn.DATASET_TYPES.value, QtCore.Qt.DescendingOrder)

    def show_new_server_dialog(self):
        self.checklist_editor_dlg = ChecklistEditor()
        self.checklist_editor_dlg.setModal(True)
        self.checklist_editor_dlg.show()
        self.checklist_editor_dlg.exec_()


