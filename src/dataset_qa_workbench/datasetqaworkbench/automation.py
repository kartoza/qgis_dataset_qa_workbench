import typing
from functools import partial
from pathlib import Path

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
        self.run_pb = QtWidgets.QPushButton('Run', parent=self)
        self.configure_pb = QtWidgets.QPushButton('Configure and run...', parent=self)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.run_pb)
        layout.addWidget(self.configure_pb)
        self.setLayout(layout)

        self.automator = ValidationStepAutomator.from_checklist_item(checklist_item_head_index, dataset)
        self.run_pb.clicked.connect(self.automator.perform_automation)
        self.configure_pb.clicked.connect(self.automator.configure_and_perform_automation)

        # self.checklist_item_head_index = checklist_item_head_index
        # utils.log_message(f'dataset type: {type(dataset)}')
        # self.dataset = dataset
        # # self.run_pb.clicked.connect(self.perform_automation)
        # do_automation = partial(external_automation, self.get_run_algorithm_parameters(), self.feedback)
        # self.run_pb.clicked.connect(do_automation)
        # self.configure_pb.clicked.connect(self.configure_automation)

    def get_automation_configuration(self) -> models.ChecklistAutomationProperty:
        checklist_item_head: models.ChecklistItemHead = (
            self.checklist_item_head_index.internalPointer().ref)
        return checklist_item_head.automation

    def get_run_algorithm_parameters(self) -> typing.Dict:
        automation = self.get_automation_configuration()
        if isinstance(self.dataset, Path):
            input_ = str(self.dataset)
        else:
            input_ = self.dataset
        utils.log_message(f'input_: {input_}')
        model = self.checklist_item_head_index.model()
        validated_idx = self.checklist_item_head_index.siblingAtColumn(1)
        notes_idx = model.index(
            ChecklistItemPropertyColumn.VALIDATION_NOTES.value, 1,
            self.checklist_item_head_index
        )
        extra_configuration = automation.to_dict()
        extra_configuration.update({
            'model': model,
            'validated_idx': validated_idx,
            'notes_idx': notes_idx,
        })
        algorithm_parameters = {
            automation.artifact_parameter_name: input_,
            '_automation_configuration': extra_configuration,
        }
        algorithm_parameters.update(automation.extra_parameters)
        return algorithm_parameters

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
        registry = QgsApplication.processingRegistry()
        automation = self.get_automation_configuration()
        algorithm = registry.createAlgorithmById(automation.algorithm_id)
        output_types = (
            QgsProcessingParameterFeatureSink,
            QgsProcessingParameterVectorDestination,
            QgsProcessingParameterRasterDestination,
        )
        algorithm_parameters = self.get_run_algorithm_parameters()
        for param in algorithm.parameterDefinitions():
            if isinstance(param, output_types):
                existing_sink: str = algorithm_parameters.get(param.name(), '')
                algorithm_parameters[param.name()] = (
                    QgsProcessingOutputLayerDefinition(existing_sink))
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        task = QgsProcessingAlgRunnerTask(
            algorithm, algorithm_parameters, context, feedback)
        # task.executed.connect(
        #     partial(automation_done, context, algorithm_parameters))
        task_manager = QgsApplication.taskManager()
        task_manager.addTask(task)
        # result = processing.Processing.runAlgorithm(
        #     algorithm,
        #     parameters=algorithm_parameters,
        #     onFinish=None,
        #     feedback=None,
        #     context=None
        # )
        # self.store_result(result)
        # utils.log_message(f'perform_automation called result was: {result}')

    def old_perform_automation(self):
        # TODO: Implement a custom processing provider and algorithm for extracting CRS from a layer
        algorithm_id, algorithm_parameters = self.get_run_algorithm_parameters()
        result = processing.run(algorithm_id, algorithm_parameters)
        self.store_result(result)
        utils.log_message(f'perform_automation called result was: {result}')

    def configure_automation(self):
        utils.log_message(f'configure_automation called')
        automation = self.get_automation_configuration()
        algorithm_parameters = self.get_run_algorithm_parameters()
        result = processing.execAlgorithmDialog(
            automation.algorithm_id, algorithm_parameters)
        self.store_result(result)


def automation_done(context, algorithm_parameters, successful, results):
    pass
    # automation = self.get_automation_configuration()
    # utils.log_message(f'output_name: {algorithm_parameters["_automation_configuration"]["output_name"]}')
    # utils.log_message(f'negate_output: {algorithm_parameters["_automation_configuration"]["negate_output"]}')
    #
    # raw_result = execution_result.get(automation.output_name, False)
    # utils.log_message(f'raw_result: {raw_result}')
    # result = bool(raw_result) if not automation.negate_output else not bool(raw_result)
    # utils.log_message(f'result: {result}')
    # utils.log_message(f'execution_result: {execution_result}')
    # model = algorithm_parameters['_automation_configuration']['model']
    # validated_idx = algorithm_parameters['_automation_configuration']['validated_idx']
    # notes_idx = algorithm_parameters['_automation_configuration']['notes_idx']
    # model.setData(
    #     validated_idx,
    #     QtCore.Qt.Checked if result else False,
    #     role=QtCore.Qt.CheckStateRole
    # )
    # if result:
    #     msg = f'Automated validation succeeded'
    # else:
    #     msg = 'Automated validation failed'
    # model.setData(notes_idx, f'{msg} - {execution_result}', role=QtCore.Qt.EditRole)
    #
    # output_layer = context.getMapLayer(results['OUTPUT'])
    # if output_layer and output_layer.isValid():
    #     QgsProject.instance().addMapLayer(
    #         context.takeResultLayer(output_layer.id())
    #     )


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
        self.algorithm = registry.createAlgorithmById(algorithm_id)
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
                existing_sink: str = self.params.get(param_def.name(), '')
                self.params[param_def.name()] = (
                    QgsProcessingOutputLayerDefinition(existing_sink))

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
            notes_idx=notes_idx
        )

    def perform_automation(self):
        task = QgsProcessingAlgRunnerTask(
            self.algorithm,
            self.params,
            self.context,
            self.feedback
        )
        task.executed.connect(self.task_finished)
        task_manager = QgsApplication.taskManager()
        task_manager.addTask(task)

    def configure_and_perform_automation(self):
        utils.log_message(f'configure_automation called')
        automation = self.get_automation_configuration()
        algorithm_parameters = self.get_run_algorithm_parameters()
        result = processing.execAlgorithmDialog(
            self.algorithm,
            self.params
        )
        utils.log_message(f'result: {result}')
        # find out if the execution has been successful, then call self.task_finished
        # self.task_finished()

    def task_finished(self, successful: bool, results: typing.Dict):
        _raw = results.get(self.output_name, False)
        utils.log_message(f'raw_result: {_raw}')
        result = bool(_raw) if not self.negate_output else not bool(_raw)
        utils.log_message(f'result: {result}')

        utils.log_message(f'successful: {successful}')

        self.model.setData(
            self.validated_idx,
            QtCore.Qt.Checked if result else False,
            role=QtCore.Qt.CheckStateRole
        )
        if result:
            msg = f'Automated validation succeeded'
        else:
            msg = 'Automated validation failed'
        self.model.setData(
            self.notes_idx, f'{msg} - {results}', role=QtCore.Qt.EditRole)


        # FIXME: This below code has to be tweaked to search for relevant output layers instead
        # output_layer = self.context.getMapLayer(results['OUTPUT'])
        # if output_layer and output_layer.isValid():
        #     QgsProject.instance().addMapLayer(
        #         self.context.takeResultLayer(output_layer.id())
        #     )

        for param_def in self.params:
            if isinstance(param_def, self._OUTPUT_TYPES):
                output_layer = self.context.getMapLayer(results[param_def.name()])
                if output_layer and output_layer.isValid():
                    QgsProject.instance().addMapLayer(
                        self.context.takeResultLayer(output_layer.id())
                    )


def external_automation(algorithm_parameters, feedback):
    registry = QgsApplication.processingRegistry()
    algorithm = registry.createAlgorithmById(algorithm_parameters['_automation_configuration']['algorithm_id'])
    output_types = (
        QgsProcessingParameterFeatureSink,
        QgsProcessingParameterVectorDestination,
        QgsProcessingParameterRasterDestination,
    )
    for param in algorithm.parameterDefinitions():
        if isinstance(param, output_types):
            existing_sink: str = algorithm_parameters.get(param.name(), '')
            algorithm_parameters[param.name()] = (
                QgsProcessingOutputLayerDefinition(existing_sink))
    context = QgsProcessingContext()
    params = algorithm_parameters.copy()
    del params["_automation_configuration"]
    task = QgsProcessingAlgRunnerTask(
        algorithm, params, context, feedback)
    # task.executed.connect(
    #     partial(automation_done, context, algorithm_parameters))
    task_manager = QgsApplication.taskManager()
    task_manager.addTask(task)