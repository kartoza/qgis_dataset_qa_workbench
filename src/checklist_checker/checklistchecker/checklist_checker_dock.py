import json
import typing
import uuid
from pathlib import Path

from qgis.gui import (
    QgsFileWidget,
    QgisInterface,
)
from qgis.core import (
    Qgis,
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
    ChecklistItemPropertyColumn,
    ChecklistModelColumn,
    CustomDataRoles,
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
    iface: QgisInterface
    tab_widget: QtWidgets.QTabWidget
    checklist_checks_tv: QtWidgets.QTreeView
    checklist_picker_dlg: ChecklistPicker
    checklist_name_le: QtWidgets.QLineEdit
    checklist_artifacts_le: QtWidgets.QLineEdit
    checklist_types_le: QtWidgets.QLineEdit
    checklist_description_te: QtWidgets.QTextEdit
    validate_file_rb: QtWidgets.QRadioButton
    validate_layer_rb: QtWidgets.QRadioButton
    layer_chooser_lv: QtWidgets.QListView
    file_chooser: QgsFileWidget
    selected_checklist: typing.Optional[models.NewCheckList]
    report_te: QtWidgets.QTextEdit
    save_report_fw: QgsFileWidget
    save_report_pb: QtWidgets.QPushButton
    tab_widget: QtWidgets.QTabWidget

    closingPlugin = QtCore.pyqtSignal()

    def __init__(self, iface: QgisInterface, parent=None):
        """Constructor."""
        super(ChecklistCheckerDock, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.save_report_pb.setDisabled(True)
        self.iface = iface
        self.checklists = []
        self.selected_checklist = None
        self.tab_widget.currentChanged.connect(self.update_tab_page)
        self.tab_widget.setTabEnabled(TabPages.CHOOSE.value, True)
        self.tab_widget.setTabEnabled(TabPages.VALIDATE.value, False)
        self.tab_widget.setTabEnabled(TabPages.REPORT.value, False)
        self.tab_pages = [self.tab_widget.widget(i.value) for i in TabPages]
        self.choose_checklist_pb.clicked.connect(self.show_checklist_picker)
        self.save_report_fw.fileChanged.connect(self.toggle_save_report_button)
        self.save_report_pb.clicked.connect(self.save_report)

    def update_tab_page(self, index: int):
        if index == TabPages.REPORT.value:
            self.update_report()

    def update_report(self):
        report = self.generate_report()
        serialized = serialize_report(report)
        self.report_te.setText(serialized)

    def generate_report(self):
        checklist_model = self.checklist_checks_tv.model()
        return get_report_contents(checklist_model)

    def toggle_save_report_button(self, current_path: str):
        if current_path:
            self.save_report_pb.setDisabled(False)
        else:
            self.save_report_pb.setDisabled(True)

    def save_report(self):
        raw_output = self.save_report_fw.filePath()
        output = Path(raw_output).resolve()
        log_message(f'output: {raw_output}')
        # TODO: Append the correct extension to file
        # TODO: Use QGIS encoding
        try:
            output.write_text(self.report_te.toPlainText(), encoding='utf-8')
        except OSError as exc:
            self.iface.messageBar().pushMessage('Error', f'Could not save validation report: {exc}', level=Qgis.Critical)
        else:
            self.iface.messageBar().pushMessage('Success', 'Validation report saved!', level=Qgis.Info)

    def selected_layer_changed(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex):
        # This does not get called when list item is deselected
        log_message(f'inside selected_layer_changed - locals: {locals()} current: {current!r} - previous: {previous!r}')
        log_message(f'current type: {type(current)}')
        log_message(f'previous type: {type(previous)}')
        log_message(f'current row: {current.row()}')
        log_message(f'previous row: {previous.row()}')
        layer_model = self.layer_chooser_lv.model()
        layer_model: QtCore.QAbstractItemModel
        layer_id = layer_model.data(current, role=LayerChooserDataRole.LAYER_IDENTIFIER.value)
        project = QgsProject.instance()
        layer = project.mapLayers()[layer_id]
        self.load_checklist_steps(current, previous)

    def load_checklist_steps(
            self,
            current: QtCore.QModelIndex,
            previous: QtCore.QModelIndex
    ):
        layer_model = self.layer_chooser_lv.model()
        layer_id = layer_model.data(
            current, role=LayerChooserDataRole.LAYER_IDENTIFIER.value)
        project = QgsProject.instance()
        layer = project.mapLayers()[layer_id]
        checks_model = QtGui.QStandardItemModel()
        checks_model.setColumnCount(2)
        utils.log_message(f'inside load_checklist_steps selected_checklist: {self.selected_checklist}')
        utils.log_message(f'selected_checklist checks: {self.selected_checklist.checks}')
        for head_check in self.selected_checklist.checks:
            head_check: models.ChecklistItemHead
            utils.log_message(f'check {head_check.name} description: {head_check.check_properties[ChecklistItemPropertyColumn.DESCRIPTION.value]}')
        checklist_checks_model = models.CheckListItemsModel(self.selected_checklist)
        self.checklist_checks_tv.setModel(checklist_checks_model)
        self.checklist_checks_tv.setTextElideMode(QtCore.Qt.ElideNone)
        self.checklist_checks_tv.setAlternatingRowColors(True)
        # self.checklist_checks_tv.setStyleSheet('QTreeView::item { padding: 10px }')
        # delegate = models.ChecklistItemsModelDelegate()
        # self.checklist_checks_tv.setItemDelegate(delegate)

    def selected_layer_selection_changed(
            self,
            selected: QtCore.QItemSelection,
            deselected: QtCore.QItemSelection
    ):
        if len(selected.indexes()) == 0:
            self.tab_widget.setTabEnabled(TabPages.VALIDATE.value, False)
            self.tab_widget.setTabEnabled(TabPages.REPORT.value, False)
            # TODO: clear the checklist steps on the VALIDATE page
        else:
            self.tab_widget.setTabEnabled(TabPages.VALIDATE.value, True)
            self.tab_widget.setTabEnabled(TabPages.REPORT.value, True)

    def show_checklist_picker(self):
        self.checklist_picker_dlg = ChecklistPicker()
        self.checklist_picker_dlg.button_box.accepted.connect(self.load_checklist)
        self.checklist_picker_dlg.setModal(True)
        self.checklist_picker_dlg.show()
        self.checklist_picker_dlg.exec_()

    def load_checklist(self):
        selected_indexes = self.checklist_picker_dlg.checklists_tv.selectedIndexes()
        if any(selected_indexes):
            self.selected_checklist = self.get_selected_checklist(
                selected_indexes[0])
            log_message(f'the selected checklist is: {self.selected_checklist.name}')
            self.reset_loaded_checklist()
            self.load_checklist_elements(self.selected_checklist)
        else:
            log_message('no checklist was selected')

    def get_selected_checklist(self, index: QtCore.QModelIndex) -> models.Checklist:
        model = index.model()
        identifier_item = model.item(index.row(), ChecklistModelColumn.IDENTIFIER.value)
        result = identifier_item.data(role=CustomDataRoles.CHECKLIST_DOWNLOADER_IDENTIFIER.value)
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

    def enable_dataset_chooser_elements(
            self,
            dataset_type: DatasetType,
            validation_artifact_type: ValidationArtifactType
    ):
        enable_layer_chooser = False
        enable_file_chooser = False
        if dataset_type in (DatasetType.VECTOR, DatasetType.RASTER):
            if validation_artifact_type == ValidationArtifactType.DATASET:
                enable_layer_chooser = True
            elif validation_artifact_type == ValidationArtifactType.STYLE:
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
            model = get_list_view_layers(dataset_type)
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


def get_report_contents(checklist_items: models.CheckListItemsModel) -> typing.Dict:
    result = {
        'name': 'Validation report',
        'item': '',
        'item_is_valid': checklist_items.result,
        'checklist': checklist_items.checklist.name,
        'dataset_type': checklist_items.checklist.dataset_type.value,
        'artifact_type': checklist_items.checklist.validation_artifact_type.value,
        'description': checklist_items.checklist.description,
        'checks': []
    }
    for row in range(checklist_items.rowCount()):
        name_idx = checklist_items.index(row, 0)
        node = name_idx.internalPointer()
        checklist_head: models.ChecklistItemHead = node.ref
        description_prop: models.ChecklistItemProperty = checklist_head.check_properties[ChecklistItemPropertyColumn.DESCRIPTION.value]
        notes_prop: models.ChecklistItemProperty = checklist_head.check_properties[ChecklistItemPropertyColumn.VALIDATION_NOTES.value]
        check = {
            'name': checklist_head.name,
            'validated': True if checklist_head.validated == QtCore.Qt.Checked else False,
            description_prop.name: description_prop.value,
            notes_prop.name: notes_prop.value,
        }
        result['checks'].append(check)
    return result


def serialize_report(report: typing.Dict) -> str:
    return json.dumps(report, indent=2)
