import typing
from pathlib import Path

from PyQt5 import uic
from PyQt5 import QtWidgets

from . import models
from . import utils
from .checklist_server_editor import ChecklistEditor

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
    available_checklist_servers_lw: QtWidgets.QListWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.new_server_pb.clicked.connect(self.show_new_server_dialog)
        self.load_known_servers()
        self.connect_to_server_pb.clicked.connect(self.download_checklists)

    def load_known_servers(self):
        # TODO: Retrieve these from the QGIS settings object
        known_servers = [
            models.ChecklistServer('test server 1', 'http://localhost:8000'),
            models.ChecklistServer('test server 2', 'http://localhost:8000'),
            models.ChecklistServer('test server 3', 'http://localhost:8000'),
        ]
        for server in known_servers:
            self.current_server_cb.addItem(server.name, userData=server)

    def download_checklists(self):
        current_server: models.ChecklistServer = self.current_server_cb.currentData()
        utils.log_message(f'current_server: {current_server.name}, {current_server.url}')
        checklist_collection_url = f'{current_server.url}checklists'
        # now use Qt's downloading facilities to download a list of checklists


    def show_new_server_dialog(self):
        self.checklist_editor_dlg = ChecklistEditor()
        self.checklist_editor_dlg.setModal(True)
        self.checklist_editor_dlg.show()
        self.checklist_editor_dlg.exec_()
