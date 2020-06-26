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
    checklist_item_head_index: QtCore.QModelIndex
    dataset: typing.Union[QgsMapLayer, str]

    def __init__(
            self,
            checklist_item_head_index: QtCore.QModelIndex,
            dataset: typing.Union[QgsMapLayer, str],
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.checklist_item_head_index = checklist_item_head_index
        utils.log_message(f'dataset type: {type(dataset)}')
        self.dataset = dataset
        layout = QtWidgets.QHBoxLayout()
        self.run_pb = QtWidgets.QPushButton('Run', parent=self)
        self.configure_pb = QtWidgets.QPushButton('Configure and run...', parent=self)
        self.run_pb.clicked.connect(self.perform_automation)
        self.configure_pb.clicked.connect(self.configure_automation)
        layout.addWidget(self.run_pb)
        layout.addWidget(self.configure_pb)
        self.setLayout(layout)

    def get_automation_configuration(self) -> models.ChecklistAutomationProperty:
        checklist_item_head: models.ChecklistItemHead = self.checklist_item_head_index.internalPointer().ref
        return checklist_item_head.automation

    def get_run_algorithm_parameters(self):
        automation = self.get_automation_configuration()
        algorithm_parameters = {
            automation.artifact_parameter_name: self.dataset,
        }
        algorithm_parameters.update(automation.extra_parameters)
        return automation.algorithm_id, algorithm_parameters

    def store_result(self, execution_result: typing.Dict):
        automation = self.get_automation_configuration()
        utils.log_message(f'automation.output_name: {automation.output_name}')
        utils.log_message(f'automation.negate_output: {automation.negate_output}')
        raw_result = execution_result.get(automation.output_name, False)
        utils.log_message(f'raw_result: {raw_result}')
        result = bool(raw_result) if not automation.negate_output else not bool(raw_result)
        utils.log_message(f'result: {result}')
        utils.log_message(f'execution_result: {execution_result}')
        model = self.checklist_item_head_index.model()
        validated_idx = self.checklist_item_head_index.siblingAtColumn(1)
        notes_idx = model.index(ChecklistItemPropertyColumn.VALIDATION_NOTES.value, 1, self.checklist_item_head_index)
        model.setData(
            validated_idx,
            QtCore.Qt.Checked if result else False,
            role=QtCore.Qt.CheckStateRole
        )
        if result:
            msg = f'Automated validation succeeded'
        else:
            msg = 'Automated validation failed'
        model.setData(notes_idx, f'{msg} - {execution_result}', role=QtCore.Qt.EditRole)

    def perform_automation(self):
        # TODO: Implement a custom processing provider and algorithm for extracting CRS from a layer
        algorithm_id, algorithm_parameters = self.get_run_algorithm_parameters()
        result = processing.run(algorithm_id, algorithm_parameters)
        self.store_result(result)
        utils.log_message(f'perform_automation called result was: {result}')

    def configure_automation(self):
        utils.log_message(f'configure_automation called')
        algorithm_id, algorithm_parameters = self.get_run_algorithm_parameters()
        result = processing.execAlgorithmDialog(algorithm_id, algorithm_parameters)
        self.store_result(result)
