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
    LayerChooserDataRole,
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

    def selected_layer_changed(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex):
        # This does not get called when list item is deselected
        log_message(f'inside selected_layer_changed - locals: {locals()} current: {current!r} - previous: {previous!r}')
        log_message(f'current type: {type(current)}')
        log_message(f'previous type: {type(previous)}')
        log_message(f'current row: {current.row()}')
        log_message(f'previous row: {previous.row()}')

    def selected_layer_selection_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        log_message(f'inside selected_layer_selection_changed - locals: {locals()} selected: {selected!r} - deselected: {deselected!r}')
        log_message(f'selected type: {type(selected)}')
        log_message(f'deselected type: {type(deselected)}')
        log_message(f'number of selected_indexes: {len(selected.indexes())}')

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
        self.checklist_artifacts_le.setText(checklist.validation_artifact_type.value)
        self.checklist_types_le.setText(checklist.dataset_type.value)
        self.checklist_description_te.setText(checklist.description)

        enable_layer_chooser = False
        enable_file_chooser = False
        if checklist.dataset_type in (DatasetType.VECTOR, DatasetType.RASTER):
            if checklist.validation_artifact_type == ValidationArtifactType.DATASET:
                enable_layer_chooser = True
            elif checklist.validation_artifact_type == ValidationArtifactType.STYLE:
                enable_layer_chooser = True
                enable_file_chooser = True
            else:
                enable_file_chooser = True
        else:
            enable_file_chooser = True
        if enable_file_chooser:
            self.validate_file_rb.setEnabled(True)
            self.validate_file_rb.setChecked(True)
            self.file_chooser.setEnabled(True)
        if enable_layer_chooser:
            self.validate_layer_rb.setEnabled(True)
            self.validate_layer_rb.setChecked(True)
            self.layer_chooser_lv.setEnabled(True)
            model = get_list_view_layers(checklist.dataset_type)
            self.layer_chooser_lv.setModel(model)
            selection_model: QtCore.QItemSelectionModel = self.layer_chooser_lv.selectionModel()
            log_message(f'selection_model: {selection_model}')
            selection_model.currentChanged.connect(self.selected_layer_changed)
            selection_model.selectionChanged.connect(self.selected_layer_selection_changed)

    def reset_loaded_checklist(self):
        self.tab_widget.setTabEnabled(TabPages.VALIDATE.value, False)
        self.tab_widget.setTabEnabled(TabPages.REPORT.value, False)

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


def get_list_view_layers(dataset_type: models.DatasetType) -> QtGui.QStandardItemModel:
    project = QgsProject.instance()
    result = QtGui.QStandardItemModel()
    for index, (id_, layer) in enumerate(project.mapLayers().items()):
        if utils.match_maplayer_type(layer.type()) == dataset_type:
            item = QtGui.QStandardItem(layer.name())
            item.setData(id_, LayerChooserDataRole.LAYER_IDENTIFIER.value)
            result.setItem(index, item)
            log_message(
                f'retrieving layer id from the '
                f'item: {item.data(LayerChooserDataRole.LAYER_IDENTIFIER.value)}'
            )
    return result


def get_legal_layers(dataset_type: models.DatasetType) -> typing.Dict[str, QgsMapLayer]:
    project = QgsProject.instance()
    result = {}
    for id_, layer in project.mapLayers().items():
        if utils.match_maplayer_type(layer.type()) == dataset_type:
            result[id_] = layer
    return result
