from pathlib import Path

from PyQt5 import uic
from PyQt5 import QtWidgets

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
UI_DIR = Path(__file__).parents[1] / "ui"
FORM_CLASS, _ = uic.loadUiType(
    str(UI_DIR / 'checklist_server_editor.ui'))


class ChecklistEditor(QtWidgets.QDialog, FORM_CLASS):
    name_le: QtWidgets.QLineEdit
    url_le: QtWidgets.QLineEdit
    button_box: QtWidgets.QDialogButtonBox

    def __init__(self, parent=None):
        super().__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.button_box.button(self.button_box.Ok).setEnabled(False)
        self.name_le.textChanged.connect(self.toggle_ok_btn)
        self.url_le.textChanged.connect(self.toggle_ok_btn)

    def toggle_ok_btn(self, text: str):
        ok_btn = self.button_box.button(self.button_box.Ok)
        if self.name_le.text() != '' and self.url_le.text() != '':
            ok_btn.setEnabled(True)
        else:
            ok_btn.setEnabled(False)
