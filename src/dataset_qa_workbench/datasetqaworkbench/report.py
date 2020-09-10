import json
import typing

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from qgis.core import (
    QgsApplication,
    QgsProcessingAlgorithm,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeedback,
)

from .models import ChecklistReport
from .constants import REPORT_HANDLER_INPUT_NAME


class ReportHandler:
    algorithm: QgsProcessingAlgorithm
    context: QgsProcessingContext
    feedback: QgsProcessingFeedback
    params: typing.Dict

    def __init__(
            self,
            report: typing.Dict,
            algorithm_id: str,
            execution_params: typing.Optional[typing.Dict] = None,
            context: typing.Optional[QgsProcessingContext] = None,
            feedback: typing.Optional[QgsProcessingFeedback] = None,
    ):
        self.context = context or QgsProcessingContext()
        self.feedback = feedback or QgsProcessingFeedback()
        registry = QgsApplication.processingRegistry()
        self.algorithm = registry.createAlgorithmById(algorithm_id)
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
        pass

    def task_finished(self, successful: bool, results: typing.Dict):
        pass


class PostValidationButtonsWidget(QtWidgets.QWidget):
    run_pb: QtWidgets.QPushButton
    configure_pb: QtWidgets.QPushButton
    report_handler: ReportHandler

    def __init__(
            self,
            report: typing.Dict,
            checklist_report: ChecklistReport,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.run_pb = QtWidgets.QPushButton('Handle report', parent=self)
        self.configure_pb = QtWidgets.QPushButton(
            'Configure and run...', parent=self)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.run_pb)
        layout.addWidget(self.configure_pb)
        self.setLayout(layout)

        self.report_handler = ReportHandler(
            report,
            checklist_report.algorithm_id,
            checklist_report.extra_parameters,
        )

        self.run_pb.clicked.connect(
            self.report_handler.handle_report)
        self.configure_pb.clicked.connect(
            self.report_handler.configure_and_handle_report)
