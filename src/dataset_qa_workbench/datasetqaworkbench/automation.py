import typing
from pathlib import Path

import processing
from PyQt5 import (
    QtCore,
    QtWidgets,
)
from qgis.core import (
    QgsApplication,
    QgsMapLayer,
    QgsProcessingAlgorithm,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterVectorDestination,
    QgsProcessingParameterRasterDestination,
    QgsProcessingOutputLayerDefinition,
    QgsProject,
)

from . import (
    models,
    utils,
)
from .constants import ChecklistItemPropertyColumn


class ValidationStepAutomator:
    algorithm: QgsProcessingAlgorithm
    context: QgsProcessingContext
    feedback: QgsProcessingFeedback
    params: typing.Dict
    output_name: str
    negate_output: bool
    model: QtCore.QAbstractItemModel
    validated_idx: QtCore.QModelIndex
    notes_idx: QtCore.QModelIndex
    _OUTPUT_TYPES = (
        QgsProcessingParameterFeatureSink,
        QgsProcessingParameterVectorDestination,
        QgsProcessingParameterRasterDestination,
    )

    def __init__(
            self,
            algorithm_id: str,
            artifact_parameter_name: str,
            output_name: str,
            negate_output: bool,
            artifact_path: typing.Union[str, Path],
            model: QtCore.QAbstractItemModel,
            validated_idx: QtCore.QModelIndex,
            notes_idx: QtCore.QModelIndex,
            execution_params: typing.Optional[typing.Dict] = None,
            context: typing.Optional[QgsProcessingContext] = None,
            feedback: typing.Optional[QgsProcessingFeedback] = None,
    ):
        self.context = context or QgsProcessingContext()
        self.feedback = feedback or QgsProcessingFeedback()
        registry = QgsApplication.processingRegistry()
        algorithm = registry.createAlgorithmById(algorithm_id)
        if algorithm is None:
            raise RuntimeError(f'Invalid algorithm_id: {algorithm_id!r}')
        self.algorithm = algorithm
        self.output_name = output_name
        self.negate_output = negate_output
        self.model = model
        self.validated_idx = validated_idx
        self.notes_idx = notes_idx
        self.params = dict(execution_params) if execution_params else {}
        if isinstance(artifact_path, Path):
            input_ = str(artifact_path)
        else:
            input_ = artifact_path
        self.params.update({artifact_parameter_name: input_})

        for param_def in self.algorithm.parameterDefinitions():
            if isinstance(param_def, self._OUTPUT_TYPES):
                out_layer_definition = QgsProcessingOutputLayerDefinition(
                    'memory:')
                out_layer_definition.createOptions = {
                    'fileEncoding': 'utf-8'
                }
                self.params[param_def.name()] = out_layer_definition

    @classmethod
    def from_checklist_item(
            cls,
            checklist_item: QtCore.QModelIndex,
            resource: typing.Union[str, Path, QgsMapLayer],
    ):
        checklist_item_head: models.ChecklistItemHead = (
            checklist_item.internalPointer().ref)
        automation: models.ChecklistAutomationProperty = (
            checklist_item_head.automation)
        model = checklist_item.model()
        notes_idx = model.index(
            ChecklistItemPropertyColumn.VALIDATION_NOTES.value,
            1,
            checklist_item
        )
        validated_idx = checklist_item.siblingAtColumn(1)
        return cls(
            automation.algorithm_id,
            automation.artifact_parameter_name,
            automation.output_name,
            automation.negate_output,
            artifact_path=resource,
            model=model,
            validated_idx=validated_idx,
            notes_idx=notes_idx,
            execution_params=automation.extra_parameters
        )

    def perform_automation(self):
        task = QgsProcessingAlgRunnerTask(
            self.algorithm,
            self.params,
            self.context,
            self.feedback
        )
        utils.log_message(f'self.algorithm: {self.algorithm}')
        utils.log_message(f'self.params: {self.params}')
        utils.log_message(f'self.params types: {[(k, type(v)) for k,v in self.params.items()]}')
        utils.log_message(f'self.params values: {[(k, v) for k,v in self.params.items()]}')
        task.executed.connect(self.task_finished)
        task_manager = QgsApplication.taskManager()
        task_manager.addTask(task)

    def configure_and_perform_automation(self):
        utils.log_message(f'configure_automation called')
        utils.log_message(f'self.algorithm: {self.algorithm}')
        utils.log_message(f'self.params: {self.params}')
        utils.log_message(f'self.params types: {[(k, type(v)) for k,v in self.params.items()]}')
        utils.log_message(f'self.params values: {[(k, v) for k,v in self.params.items()]}')
        accepted, result = utils.execute_algorithm_dialog(
            self.algorithm, self.params)
        # result = processing.execAlgorithmDialog(
        #     self.algorithm,
        #     self.params
        # )
        if accepted:
            utils.log_message(f'result: {result}')
            successful = bool(result) if result is not None else False
            self.task_finished(successful, result)

    def task_finished(self, successful: bool, results: typing.Dict):
        utils.log_message(f'successful: {successful}')
        utils.log_message(f'results: {results}')
        if successful:
            _raw = results.get(self.output_name, False)
            utils.log_message(f'raw_result: {_raw}')
            result = bool(_raw) if not self.negate_output else not bool(_raw)
            if result:
                msg = f'Automated validation succeeded'
            else:
                msg = 'Automated validation failed'
            utils.log_message(f'result: {result}')
            self.model.setData(
                self.validated_idx,
                QtCore.Qt.Checked if result else False,
                role=QtCore.Qt.CheckStateRole
            )
            self.model.setData(
                self.notes_idx, f'{msg} - {results}', role=QtCore.Qt.EditRole)


class AutomationButtonsWidget(QtWidgets.QWidget):
    run_pb: QtWidgets.QPushButton
    configure_pb: QtWidgets.QPushButton
    checklist_item_head_index: QtCore.QModelIndex
    dataset: typing.Union[QgsMapLayer, str]
    automator: ValidationStepAutomator

    def __init__(
            self,
            checklist_item_head_index: QtCore.QModelIndex,
            dataset: typing.Union[QgsMapLayer, str],
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.run_pb = QtWidgets.QPushButton('Run', parent=self)
        self.configure_pb = QtWidgets.QPushButton(
            'Configure and run...', parent=self)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.run_pb)
        layout.addWidget(self.configure_pb)
        self.setLayout(layout)

        self.automator = ValidationStepAutomator.from_checklist_item(
            checklist_item_head_index, dataset)
        self.run_pb.clicked.connect(self.automator.perform_automation)
        self.configure_pb.clicked.connect(
            self.automator.configure_and_perform_automation)