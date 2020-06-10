import typing
import uuid
from pathlib import Path

from qgis.gui import QgsFileWidget
from qgis.core import (
    QgsMapLayer,
    QgsMapLayerType,
    QgsProject,
)
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from . import models
from . import utils
from .checklist_picker import ChecklistPicker
from .constants import (
    ChecklistModelColumn,
    DatasetType,
    TabPages,
    ValidationArtifactType,
)
from .utils import log_message

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
UI_DIR = Path(__file__).parents[1] / "ui"
FORM_CLASS, _ = uic.loadUiType(
    str(UI_DIR / 'checklist_checker_dock.ui'))


class ChecklistCheckerDock(QtWidgets.QDockWidget, FORM_CLASS):
    tab_widget: QtWidgets.QTabWidget
    checklist_picker_dlg: ChecklistPicker
    checklist_name_le: QtWidgets.QLineEdit
    checklist_artifacts_le: QtWidgets.QLineEdit
    checklist_types_le: QtWidgets.QLineEdit
    checklist_description_te: QtWidgets.QTextEdit
    validate_file_rb: QtWidgets.QRadioButton
    validate_layer_rb: QtWidgets.QRadioButton
    layer_chooser_lv: QtWidgets.QListView
    file_chooser: QgsFileWidget

    closingPlugin = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(ChecklistCheckerDock, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.checklists = []
        self.tab_widget: QtWidgets.QTabWidget
        self.tab_widget.setTabEnabled(TabPages.CHOOSE.value, True)
        self.tab_widget.setTabEnabled(TabPages.VALIDATE.value, False)
        self.tab_widget.setTabEnabled(TabPages.REPORT.value, False)
        self.tab_pages = [self.tab_widget.widget(i.value) for i in TabPages]
        self.choose_checklist_pb.clicked.connect(self.show_checklist_picker)
        self.layer_chooser_lv.clicked.connect(self.enable_validation_page)

    def show_checklist_picker(self):
        self.checklists = self.get_checklists()
        self.checklist_picker_dlg = ChecklistPicker(self.checklists)
        self.checklist_picker_dlg.button_box.accepted.connect(self.load_checklist)
        self.checklist_picker_dlg.setModal(True)
        self.checklist_picker_dlg.show()
        self.checklist_picker_dlg.exec_()

    def enable_validation_page(self, model_index: QtCore.QModelIndex):
        log_message(f'inside enable_validation_page - model_index: {model_index}')
        self.tab_widget.setTabEnabled(TabPages.VALIDATE.value, True)
        #validation_page = self.tab_pages[TabPages.VALIDATE.value]

    def get_checklists(self):
        checklists = models.load_checklists()
        return checklists

    def load_checklist(self):
        selected_indexes = self.checklist_picker_dlg.checklists_tv.selectedIndexes()
        if any(selected_indexes):
            selected_checklist = self.get_selected_checklist(selected_indexes[0])
            log_message(f'the selected checklist is: {selected_checklist.name}')
            self.reset_loaded_checklist()
            self.load_checklist_elements(selected_checklist)
        else:
            log_message('no checklist was selected')

    def get_selected_checklist(self, index: QtCore.QModelIndex) -> models.Checklist:
        model = index.model()
        identifier_item = model.item(index.row(), ChecklistModelColumn.IDENTIFIER.value)
        log_message(f'item_data: {identifier_item.data(QtCore.Qt.DisplayRole)}')
        checklist_id = uuid.UUID(identifier_item.data(QtCore.Qt.DisplayRole))
        for checklist in self.checklists:
            if checklist.identifier == checklist_id:
                result = checklist
                break
        else:
            result = None
        return result

    def load_checklist_elements(self, checklist: models.Checklist):
        self.checklist_name_le.setEnabled(True)
        self.checklist_artifacts_le.setEnabled(True)
        self.checklist_types_le.setEnabled(True)
        self.checklist_description_te.setEnabled(True)
        self.checklist_name_le.setText(checklist.name)
        self.checklist_artifacts_le.setText(', '.join(i.value for i in checklist.validation_artifact_types))
        self.checklist_types_le.setText(', '.join(i.value for i in checklist.dataset_types))
        self.checklist_description_te.setText(checklist.description)

        file_based_artifacts = [
            ValidationArtifactType.METADATA,
            ValidationArtifactType.STYLE
        ]
        file_based_dataset_types = [
            DatasetType.DOCUMENT,
        ]
        # artifact_is_file_based = False
        # dataset_type_is_file_based = False
        # for validation_artifact in checklist.validation_artifact_types:
        #     if validation_artifact in file_based_artifacts:
        #         artifact_is_file_based = True
        #         break
        # for dataset_type in checklist.dataset_types:
        #     if dataset_type in file_based_dataset_types:
        #         dataset_type_is_file_based = True
        #         break
        # if artifact_is_file_based or dataset_type_is_file_based:
        #     self.validate_file_rb.setEnabled(True)
        #     self.validate_file_rb.setChecked(True)
        #     self.file_chooser.setEnabled(True)

        # TODO - Check logic of switcher
        # -  for vector and raster datasets we want to enable only the layer chooser
        # -  for document datasets we want to enable only the file chooser
        # -  for vector, raster and document metadata we want to enable only the file chooser
        # -  for vector and raster styles we want to enable both the layer and file chooser
        if models.DatasetType.DOCUMENT in checklist.dataset_types:
            self.validate_file_rb.setEnabled(True)
            self.validate_file_rb.setChecked(True)
            self.file_chooser.setEnabled(True)
        if models.DatasetType.VECTOR in checklist.dataset_types or models.DatasetType.RASTER in checklist.dataset_types:
            self.validate_layer_rb.setEnabled(True)
            self.validate_layer_rb.setChecked(True)
            self.layer_chooser_lv.setEnabled(True)
            model = get_list_view_layers(checklist.dataset_types)
            self.layer_chooser_lv.setModel(model)

    def reset_loaded_checklist(self):
        self.checklist_name_le.setEnabled(False)
        self.checklist_artifacts_le.setEnabled(False)
        self.checklist_types_le.setEnabled(False)
        self.checklist_description_te.setEnabled(False)
        self.validate_layer_rb.setEnabled(False)
        self.validate_file_rb.setEnabled(False)
        self.file_chooser.setEnabled(False)
        self.layer_chooser_lv.setEnabled(False)

        self.checklist_name_le.clear()
        self.checklist_artifacts_le.clear()
        self.checklist_types_le.clear()
        self.checklist_description_te.clear()
        self.validate_layer_rb.setChecked(False)
        self.validate_file_rb.setChecked(False)
        # TODO: clear loaded layers list view
        # TODO: clear file chooser


    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.closingPlugin.emit()
        event.accept()


def get_list_view_layers(dataset_types: typing.List[models.DatasetType]) -> QtGui.QStandardItemModel:
    legal_layers = get_legal_layers(dataset_types)
    result = QtGui.QStandardItemModel(len(legal_layers), 1)
    for index, (id_, layer) in enumerate(legal_layers.items()):
        result.setItem(index, QtGui.QStandardItem(layer.name()))
    return result

def get_legal_layers(dataset_types: typing.List[models.DatasetType]) -> typing.Dict[str, QgsMapLayer]:
    project = QgsProject.instance()
    result = {}
    for id_, layer in project.mapLayers().items():
        if utils.match_maplayer_type(layer.type()) in dataset_types:
            result[id_] = layer
    return result
