import json
import typing

import processing
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsProcessingAlgorithm,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeedback,
)
from qgis.gui import QgisInterface

from . import utils
from .constants import REPORT_HANDLER_INPUT_NAME


class ReportHandler:
    algorithm: QgsProcessingAlgorithm
    context: QgsProcessingContext
    feedback: QgsProcessingFeedback
    params: typing.Dict

    def __init__(
            self,
            iface: QgisInterface,
            report: typing.Dict,
            algorithm_id: str,
            execution_params: typing.Optional[typing.Dict] = None,
            context: typing.Optional[QgsProcessingContext] = None,
            feedback: typing.Optional[QgsProcessingFeedback] = None,
    ):
        self.iface = iface
        self.context = context or QgsProcessingContext()
        self.feedback = feedback or QgsProcessingFeedback()
        registry = QgsApplication.processingRegistry()
        algorithm = registry.createAlgorithmById(algorithm_id)
        if algorithm is None:
            raise RuntimeError(f'Invalid algorithm_id: {algorithm_id}')
        self.algorithm = algorithm
        self.params = dict(execution_params) if execution_params else {}
        self.params.update({REPORT_HANDLER_INPUT_NAME: json.dumps(report)})

    def handle_report(self):
        task = QgsProcessingAlgRunnerTask(
            self.algorithm,
            self.params,
            self.context,
            self.feedback
        )
        task.executed.connect(self.task_finished)
        task_manager = QgsApplication.taskManager()
        task_manager.addTask(task)

    def configure_and_handle_report(self):
        accepted, result = utils.execute_algorithm_dialog(
            self.algorithm, self.params)
        # result = processing.execAlgorithmDialog(
        #     self.algorithm,
        #     self.params
        # )
        utils.log_message(f'accepted: {accepted}')
        utils.log_message(f'result: {result}')
        if accepted:
            successful = bool(result) if result is not None else False
            self.task_finished(successful, result)

    def task_finished(self, successful: bool, results: typing.Dict):
        if successful:
            msg = f'Post validation succeeded'
            level = Qgis.Info
        else:
            msg = f'Post validation failed'
            level = Qgis.Warning
        self.iface.messageBar().pushMessage(msg, level=level, duration=3)
