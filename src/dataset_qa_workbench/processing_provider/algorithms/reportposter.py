import json
import typing

from PyQt5.QtNetwork import (
    QNetworkRequest,
)
from PyQt5.QtCore import QUrl
from qgis.core import (
    QgsNetworkAccessManager,
    QgsProcessingOutputBoolean,
    QgsProcessingOutputNumber,
    QgsProcessingOutputString,
    QgsProcessingException,
    QgsProcessingParameterAuthConfig,
    QgsProcessingParameterExpression,
    QgsProcessingParameterString,
)

from ...datasetqaworkbench.constants import (
    QGIS_VARIABLE_PREFIX,
    REPORT_HANDLER_INPUT_NAME,
)

from .base import (
    BaseAlgorithm,
    parse_as_expression,
)


class ReportPosterAlgorithm(BaseAlgorithm):
    INPUT_AUTH_CONFIG = "INPUT_AUTH_CONFIG"
    INPUT_ENDPOINT = "INPUT_ENDPOINT"
    OUTPUT_REQUEST_ACCEPTED = "OUTPUT_REQUEST_ACCEPTED"
    OUTPUT_RESPONSE_STATUS_CODE = "OUTPUT_RESPONSE_STATUS_CODE"

    def name(self):
        return "reportposter"

    def displayName(self):
        return self.tr("Report poster")

    def createInstance(self):
        return ReportPosterAlgorithm()

    def shortHelpString(self):
        return self.tr(
            "This algorithm will post the generated validation report to a "
            "remote host.\n\n"
            "In order to be easily automatable, the algorithm can be "
            "configured by setting the following QGIS global variables "
            "(go to Settings -> Options... -> Variables): "
            "\n\n"
            "- dataset_qa_workbench_auth_config_id: auth config id of the "
            "credentials to use to authenticate with the remote API\n"
            "- dataset_qa_workbench_endpoint: Enpoint of the remote API"
        )

    def initAlgorithm(self, configuration, p_str=None, Any=None, *args, **kwargs):
        self.addParameter(
            QgsProcessingParameterString(
                REPORT_HANDLER_INPUT_NAME,
                self.tr("Input validation report"),
                defaultValue="{}",
                multiLine=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_AUTH_CONFIG,
                self.tr("Authentication configuration ID"),
                defaultValue=f"@{QGIS_VARIABLE_PREFIX}_auth_config_id",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_ENDPOINT,
                self.tr("remote URL endpoint"),
                defaultValue=f"@{QGIS_VARIABLE_PREFIX}_endpoint",
            )
        )
        self.addOutput(
            QgsProcessingOutputBoolean(
                self.OUTPUT_REQUEST_ACCEPTED, "Was the request accepted or not"
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT_RESPONSE_STATUS_CODE, "status code of the response"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        raw_report = self.parameterAsString(
            parameters, REPORT_HANDLER_INPUT_NAME, context
        )
        report = json.loads(raw_report)

        auth_config = parse_as_expression(
            self.parameterAsExpression(parameters, self.INPUT_AUTH_CONFIG, context)
        )

        endpoint = parse_as_expression(
            self.parameterAsExpression(parameters, self.INPUT_ENDPOINT, context)
        )
        if not endpoint:
            raise QgsProcessingException(f"Invalid endpoint: {endpoint}")
        request = QNetworkRequest(QUrl(endpoint))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")

        network_manager = QgsNetworkAccessManager.instance()
        reply = network_manager.blockingPost(
            request,
            json.dumps(report).encode("utf-8"),
            auth_config if auth_config is not None else "",
            True,
            feedback,
        )
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        feedback.pushInfo(f"status_code: {status_code}")
        return {self.OUTPUT_RESPONSE_STATUS_CODE: status_code}
