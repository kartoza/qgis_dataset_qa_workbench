import datetime as dt
import json
import typing
from pathlib import Path
from sys import getfilesystemencoding

from qgis.gui import (
    QgsFileWidget,
    QgisInterface,
)
from qgis.core import (
    Qgis,
    QgsExpressionContextUtils,
    QgsMapLayer,
    QgsLayerMetadata,
    QgsMapLayerType,
    QgsProject,
)
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtPrintSupport import QPrinter

from . import models
from . import utils
from .automation import AutomationButtonsWidget
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
    str(UI_DIR / 'dataset_qa_workbench_dock.ui'))


class DatasetQaWorkbenchDock(QtWidgets.QDockWidget, FORM_CLASS):
    add_report_to_layer_metadata_pb: QtWidgets.QPushButton
    dataset: typing.Optional[typing.Union[QgsMapLayer, str]]
    iface: QgisInterface
    tab_widget: QtWidgets.QTabWidget
    checklist_checks_tv: models.MyTreeView
    checklist_picker_dlg: ChecklistPicker
    checklist_name_le: QtWidgets.QLineEdit
    checklist_artifacts_le: QtWidgets.QLineEdit
    checklist_types_le: QtWidgets.QLineEdit
    checklist_description_te: QtWidgets.QTextEdit
    choose_checklist_pb: QtWidgets.QPushButton
    clear_checks_pb: QtWidgets.QPushButton
    validate_file_rb: QtWidgets.QRadioButton
    validate_layer_rb: QtWidgets.QRadioButton
    layer_chooser_lv: QtWidgets.QListView
    file_chooser: QgsFileWidget
    selected_checklist: typing.Optional[models.CheckList]
    report_te: QtWidgets.QTextEdit
    save_report_fw: QgsFileWidget
    save_report_pb: QtWidgets.QPushButton
    tab_widget: QtWidgets.QTabWidget

    closingPlugin = QtCore.pyqtSignal()

    def __init__(self, iface: QgisInterface, parent=None):
        """Constructor."""
        super(DatasetQaWorkbenchDock, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.dataset = None
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
        self.add_report_to_layer_metadata_pb.clicked.connect(self.add_report_to_layer_metadata)
        self.clear_checks_pb.clicked.connect(self.clear_all_checks)
        self.automate_all_checks_pb.clicked.connect(self.automate_all_checks)
        self.file_chooser.fileChanged.connect(self.selected_file_changed)
        self.validate_layer_rb.toggled.connect(self.respond_to_validate_layer_rb_toggled)
        # TODO: It might be necessary to disconnect these when plugin is unloaded
        QgsProject.instance().layersAdded.connect(self.respond_to_layers_added)
        QgsProject.instance().layersRemoved.connect(self.respond_to_layers_removed)

    def respond_to_layers_added(self, layers):
        utils.log_message('layers added')
        if self.selected_checklist is not None:
            current_dataset_type = self.selected_checklist.dataset_type
            model: QtGui.QStandardItemModel = self.layer_chooser_lv.model()
            for layer in layers:
                if utils.match_maplayer_type(layer.type()) == current_dataset_type:
                    item = QtGui.QStandardItem(layer.name())
                    item.setData(layer.id(), LayerChooserDataRole.LAYER_IDENTIFIER.value)
                    model.appendRow([item])

    def respond_to_layers_removed(self, layers: typing.List[str]):
        utils.log_message('layers removed')
        model: QtGui.QStandardItemModel = self.layer_chooser_lv.model()
        if model is not None:
            for row_idx in reversed(range(model.rowCount())):
                index = model.index(row_idx, 0)
                item = model.itemFromIndex(index)
                if item.data() in layers:
                    model.removeRow(row_idx)


    def clear_all_checks(self):
        utils.log_message(f'clear_all_checks_called')
        model = self.checklist_checks_tv.model()
        for row_index in range(model.rowCount()):
            utils.log_message(f'Unchecking row {row_index}...')
            checkbox_index = model.index(row_index, 1)
            model.setData(checkbox_index, QtCore.Qt.Unchecked, role=QtCore.Qt.CheckStateRole)
            head_index = model.index(row_index, 0)
            notes_index = model.index(
                ChecklistItemPropertyColumn.VALIDATION_NOTES.value,
                1,
                parent=head_index
            )
            model.setData(notes_index, '', role=QtCore.Qt.EditRole)

    def automate_all_checks(self):
        utils.log_message(f'automate_all_checks_called')
        model = self.checklist_checks_tv.model()
        for row_index in range(model.rowCount()):
            item_head_index = model.index(row_index, 0)
            automation_index = model.index(ChecklistItemPropertyColumn.AUTOMATION.value, 1, parent=item_head_index)
            automation_widget = self.checklist_checks_tv.indexWidget(automation_index)
            if automation_widget:
                automation_widget.perform_automation()


    def update_tab_page(self, index: int):
        if index == TabPages.REPORT.value:
            self.update_report()
            self.add_report_to_layer_metadata_pb.setEnabled(self.validate_layer_rb.isChecked())

    def update_report(self):
        if self.validate_layer_rb.isChecked():
            current_layer_idx = self.layer_chooser_lv.currentIndex()
            layer_model = self.layer_chooser_lv.model()
            layer_id = layer_model.data(
                current_layer_idx, role=LayerChooserDataRole.LAYER_IDENTIFIER.value)
            project = QgsProject.instance()
            layer = project.mapLayers()[layer_id]
            dataset = layer
        else:
            # TODO: Implement report generation for datasets that are not layers
            dataset = None
        report = self.generate_report(dataset)
        if report:
            serialized = serialize_report_to_html(report)
            self.report_te.setDocument(serialized)

    def generate_report(self, dataset: typing.Union[QgsMapLayer, str]):
        checklist_model = self.checklist_checks_tv.model()
        if checklist_model is not None:
            result = get_report_contents(checklist_model, dataset)
        else:
            result = None
        return result

    def toggle_save_report_button(self, current_path: str):
        if current_path:
            self.save_report_pb.setDisabled(False)
        else:
            self.save_report_pb.setDisabled(True)

    def save_report(self):
        output = get_report_path(self.save_report_fw.filePath())
        printer = QPrinter(QPrinter.PrinterResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setPaperSize(QPrinter.A4)
        printer.setOutputFileName(str(output))
        doc: QtGui.QTextDocument = self.report_te.document().clone()
        page_size = printer.pageRect().size()
        doc.setPageSize(QtCore.QSizeF(page_size.width(), page_size.height()))
        doc.print(printer)
        if output.is_file():
            # `doc.print` does not return a value, so this is a hacky way to
            # check if the file was saved correctly
            self.iface.messageBar().pushMessage(
                'Success',
                'Validation report saved!',
                level=Qgis.Info
            )
        else:
            self.iface.messageBar().pushMessage(
                'Error',
                f'Could not save validation report to: {output}',
                level=Qgis.Critical
            )

    def add_report_to_layer_metadata(self):
        report = self.generate_report(dataset=self.dataset)
        add_report_to_layer(report, self.dataset)
        self.iface.messageBar().pushMessage(
            'Success', 'Validation report added to layer metadata!',
            level=Qgis.Info
        )

    def selected_layer_changed(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex):
        # NOTE: This method does not get called when list item is deselected
        self.dataset = self._get_current_layer()
        if self.dataset:
            self.load_checklist_steps(current, previous)

    def load_checklist_steps(
            self,
            current: QtCore.QModelIndex,
            previous: QtCore.QModelIndex
    ):
        utils.log_message(f'inside load_checklist_steps selected_checklist: {self.selected_checklist}')
        utils.log_message(f'selected_checklist checks: {self.selected_checklist.checks}')
        for head_check in self.selected_checklist.checks:
            head_check: models.ChecklistItemHead
            utils.log_message(
                f'check {head_check.name} description: '
                f'{head_check.check_properties[ChecklistItemPropertyColumn.DESCRIPTION.value]}'
            )
        checklist_checks_model = models.CheckListItemsModel(self.selected_checklist)
        self.checklist_checks_tv.setModel(checklist_checks_model)
        self.checklist_checks_tv.resized.connect(self.force_model_update)
        self.checklist_checks_tv.setTextElideMode(QtCore.Qt.ElideNone)
        self.checklist_checks_tv.setWordWrap(True)
        self.checklist_checks_tv.setAlternatingRowColors(True)
        self.add_automation_widgets()
        header = self.checklist_checks_tv.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        delegate = models.ChecklistItemsModelDelegate(self.checklist_checks_tv)
        self.checklist_checks_tv.setItemDelegate(delegate)

    def add_automation_widgets(self):
        model = self.checklist_checks_tv.model()
        for head_row in range(model.rowCount()):
            head_index = model.index(head_row, 0)
            item_head: models.ChecklistItemHead = head_index.internalPointer().ref
            if item_head.automation.algorithm_id is not None:
                automation_index = model.index(ChecklistItemPropertyColumn.AUTOMATION.value, 1, head_index)
                automation_widget = AutomationButtonsWidget(checklist_item_head_index=head_index, dataset=self.dataset)
                self.checklist_checks_tv.setIndexWidget(automation_index, automation_widget)

    def force_model_update(self):
        model = self.checklist_checks_tv.model()
        for row in range(model.rowCount()):
            parent = model.index(row, 0)
            properties = (
                ChecklistItemPropertyColumn.DESCRIPTION.value,
                ChecklistItemPropertyColumn.GUIDE.value,
                ChecklistItemPropertyColumn.VALIDATION_NOTES.value
            )
            for property_row in properties:
                property_index = model.index(property_row, 1, parent)
                model.dataChanged.emit(property_index, property_index)

    def selected_file_changed(self, raw_path: str):
        utils.log_message(f'selected_file_changed raw_path: {raw_path}')
        if raw_path and self.validate_file_rb.isChecked():
            self.toggle_other_pages(True)
            self.dataset = Path(raw_path).expanduser().resolve()
            self.load_checklist_steps(None, None)
        elif not raw_path and self.validate_file_rb.isChecked():
            self.toggle_other_pages(False)
            self.dataset = None

    def toggle_other_pages(self, enabled: bool):
        self.tab_widget.setTabEnabled(TabPages.VALIDATE.value, enabled)
        self.tab_widget.setTabEnabled(TabPages.REPORT.value, enabled)

    def respond_to_validate_layer_rb_toggled(self, checked: bool):
        if checked:
            self.layer_chooser_lv.setEnabled(True)
            self.file_chooser.setEnabled(False)
            try:
                current_layer_selection: QtCore.QItemSelection = self.layer_chooser_lv.selectionModel().selection()
            except AttributeError:
                pass
            else:
                self.selected_layer_selection_changed(current_layer_selection, None)
        else:
            self.layer_chooser_lv.setEnabled(False)
            self.file_chooser.setEnabled(True)
            self.selected_file_changed(self.file_chooser.filePath())

    def selected_layer_selection_changed(
            self,
            selected: QtCore.QItemSelection,
            deselected: QtCore.QItemSelection
    ):
        if len(selected.indexes()) > 0 and self.validate_layer_rb.isChecked():
            self.toggle_other_pages(True)
            # TODO: check if self.dataset is None
            self.dataset = self._get_current_layer()
        elif len(selected.indexes()) == 0 and self.validate_layer_rb.isChecked():
            self.toggle_other_pages(False)
            self.dataset = None

    def _get_current_layer(self) -> typing.Optional[QgsMapLayer]:
        current_layer_idx = self.layer_chooser_lv.currentIndex()
        utils.log_message(f'current_layer_idx: {current_layer_idx}')
        if current_layer_idx == QtCore.QModelIndex():
            result = None
        else:
            layer_model = self.layer_chooser_lv.model()
            layer_id = layer_model.data(
                current_layer_idx, role=LayerChooserDataRole.LAYER_IDENTIFIER.value)
            utils.log_message(f'layer_id: {layer_id}')
            layer_model = self.layer_chooser_lv.model()
            project = QgsProject.instance()
            result = project.mapLayers()[layer_id]
        return result

    def show_checklist_picker(self):
        self.checklist_picker_dlg = ChecklistPicker(self.iface)
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

    def get_selected_checklist(self, index: QtCore.QModelIndex) -> models.CheckList:
        model = index.model()
        identifier_item = model.item(index.row(), ChecklistModelColumn.IDENTIFIER.value)
        result = identifier_item.data(role=CustomDataRoles.CHECKLIST_DOWNLOADER_IDENTIFIER.value)
        return result

    def load_checklist_elements(self, checklist: models.CheckList):
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
            self.selected_file_changed(self.file_chooser.filePath())
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


def get_list_view_layers(dataset_type: DatasetType) -> QtGui.QStandardItemModel:
    project = QgsProject.instance()
    result = QtGui.QStandardItemModel()
    for index, (id_, layer) in enumerate(project.mapLayers().items()):
        if utils.match_maplayer_type(layer.type()) == dataset_type:
            item = QtGui.QStandardItem(layer.name())
            item.setData(id_, LayerChooserDataRole.LAYER_IDENTIFIER.value)
            result.appendRow([item])
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


def get_report_contents(
        checklist_items: models.CheckListItemsModel,
        dataset: typing.Union[QgsMapLayer, str]
) -> typing.Dict:
    global_scope = QgsExpressionContextUtils.globalScope()
    if isinstance(dataset, QgsMapLayer):
        name = dataset.name()
    else:
        name = dataset
    result = {
        'name': 'Validation report',
        'validator': global_scope.variable('user_full_name'),
        'generated': dt.datetime.now(dt.timezone.utc).isoformat(),
        'dataset': name,
        'dataset_is_valid': checklist_items.result,
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
            'description': checklist_head.description,
            'notes': checklist_head.validation_notes,
        }
        result['checks'].append(check)
    return result


def serialize_report(report: typing.Dict) -> str:
    return json.dumps(report, indent=2)


def serialize_report_to_html(report: typing.Dict) -> QtGui.QTextDocument:
    validation_check_template_path = ':/plugins/dataset_qa_workbench/validation-report-check-template.html'
    check_template_fh = QtCore.QFile(validation_check_template_path)
    check_template_fh.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text)
    check_template = check_template_fh.readAll().data().decode(getfilesystemencoding())
    check_template_fh.close()
    rendered_checks = []
    utils.log_message('Rendering checks...')
    for check in report.get('checks', []):
        rendered = check_template.format(
            check_name=check['name'],
            validated='YES' if check['validated'] else 'NO',
            description=check['description'],
            notes=check['notes'].replace('{', '{{').replace('}', '}}'),
        )
        utils.log_message(f'check {rendered}')
        rendered_checks.append(rendered)
    utils.log_message('Rendering final report...')
    validation_report_template_path = ':/plugins/dataset_qa_workbench/validation-report-template.html'
    report_template_fh = QtCore.QFile(validation_report_template_path)
    report_template_fh.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text)
    report_template = report_template_fh.readAll().data().decode(getfilesystemencoding())
    report_template_fh.close()
    ready_to_render = report_template.replace('{checks}', '\n'.join(rendered_checks))
    utils.log_message(f'Replaced checks placeholder: {report_template}')
    rendered_report = ready_to_render.format(
        checklist_name=report['checklist'],
        dataset_name=report['dataset'],
        timestamp=report['generated'],
        result=report['dataset_is_valid'],
        author=report['validator'],
        description=report['description'],
    )
    doc = QtGui.QTextDocument()
    doc.setHtml(rendered_report)
    return doc


def serialize_report_to_plain_text(report: typing.Dict) -> str:
    validation_check_template_path = ':/plugins/dataset_qa_workbench/validation-report-check-template.txt'
    check_template_fh = QtCore.QFile(validation_check_template_path)
    check_template_fh.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text)
    check_template = check_template_fh.readAll().data().decode(getfilesystemencoding())
    check_template_fh.close()
    rendered_checks = []
    utils.log_message('Rendering checks...')
    for check in report.get('checks', []):
        rendered = check_template.format(
            check_name=check['name'],
            validated='YES' if check['validated'] else 'NO',
            description=check['description'],
            notes=check['notes'].replace('{', '{{').replace('}', '}}'),
        )
        utils.log_message(f'check {rendered}')
        rendered_checks.append(rendered)
    utils.log_message('Rendering final report...')
    validation_report_template_path = ':/plugins/dataset_qa_workbench/validation-report-template.txt'
    report_template_fh = QtCore.QFile(validation_report_template_path)
    report_template_fh.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text)
    report_template = report_template_fh.readAll().data().decode(getfilesystemencoding())
    report_template_fh.close()
    ready_to_render = report_template.replace('{checks}', '\n'.join(rendered_checks))
    utils.log_message(f'Replaced checks placeholder: {report_template}')
    rendered_report = ready_to_render.format(
        checklist_name=report['checklist'],
        dataset_name=report['dataset'],
        timestamp=report['generated'],
        result=report['dataset_is_valid'],
        author=report['validator'],
        description=report['description'],
    )
    return rendered_report


def add_report_to_layer(report: typing.Dict, layer: QgsMapLayer):
    history_msg = (
        f'{report["generated"]} - Validation report: '
        f'{"Valid" if report["dataset_is_valid"] else "Invalid"}'
    )
    abstract_msg = serialize_report_to_plain_text(report)
    metadata: QgsLayerMetadata = layer.metadata()
    history: typing.List = metadata.history()
    history.append(history_msg)
    abstract: str = metadata.abstract()
    abstract = '\n\n---\n\n'.join((abstract, abstract_msg))
    metadata.setAbstract(abstract)
    metadata.setHistory(history)
    layer.setMetadata(metadata)


def get_report_path(raw_path: str) -> Path:
    result = Path(raw_path).expanduser().resolve()
    if result.suffix.lower() != '.pdf':
        result = result.parent / f'{result.name}.pdf'
    return result
