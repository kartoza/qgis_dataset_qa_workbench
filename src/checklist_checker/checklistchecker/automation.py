import typing

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)
from qgis.core import (
    QgsApplication,
    QgsMapLayer,
)
import processing

from . import (
    models,
    utils,
)
from .constants import ChecklistItemPropertyColumn


class AutomationButtonsWidget(QtWidgets.QWidget):
    run_pb: QtWidgets.QPushButton
    configure_pb: QtWidgets.QPushButton
    checklist_items_model: models.CheckListItemsModel
    model_index: QtCore.QModelIndex
    dataset: typing.Union[QgsMapLayer, str]

    def __init__(
            self,
            checklist_items_model: models.CheckListItemsModel,
            index: QtCore.QModelIndex,
            dataset: typing.Union[QgsMapLayer, str],
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.checklist_items_model = checklist_items_model
        self.model_index = index
        self.dataset = dataset
        layout = QtWidgets.QHBoxLayout()
        self.run_pb = QtWidgets.QPushButton('Run', parent=self)
        self.configure_pb = QtWidgets.QPushButton('Configure and run...', parent=self)
        self.run_pb.clicked.connect(self.perform_automation)
        self.configure_pb.clicked.connect(self.configure_automation)
        layout.addWidget(self.run_pb)
        layout.addWidget(self.configure_pb)
        self.setLayout(layout)

    def _get_automation_property(self) -> models.ChecklistItemProperty:
        automation_index: QtCore.QModelIndex = self.checklist_items_model.index(
            ChecklistItemPropertyColumn.AUTOMATION.value, 1, self.model_index)
        return automation_index.internalPointer().ref

    def perform_automation(self):
        check_prop: models.ChecklistItemProperty = self._get_automation_property()
        serialized_automation = check_prop.value
        algorithm_id = serialized_automation
        processing_registry = QgsApplication.processingRegistry()
        algorithm = processing_registry.algorithmById(algorithm_id)
        # TODO: Implement a custom processing provider and algorithm for extracting CRS from a layer
        if algorithm is not None:
            algorithm_parameters = {
                'INPUT': self.dataset,
                'OUTPUT': 'memory:'
            }
            result = processing.run(algorithm_id, algorithm_parameters)
        utils.log_message(f'perform_automation called result was: {result}')

    def configure_automation(self):
        utils.log_message(f'configure_automation called')
        check_prop: models.ChecklistItemProperty = self._get_automation_property()
        serialized_automation = check_prop.value
        algorithm_id = serialized_automation
        algorithm_parameters = {}
        result = processing.execAlgorithmDialog(algorithm_id, algorithm_parameters)
        utils.log_message(f'result: {result}')
