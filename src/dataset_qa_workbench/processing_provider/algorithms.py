import json
import smtplib
from email.message import EmailMessage

from PyQt5 import (
    QtCore,
    QtGui,
)
from qgis.core import (
    QgsFeatureSink,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingOutputBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterExpression,
    QgsProcessingParameterMapLayer,
    QgsProcessingParameterString,
)


class BaseAlgorithm(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Algorithms from checklist checker plugin'

    def tr(self, string):
        return QtCore.QCoreApplication.translate('Processing', string)

    def icon(self):
        return QtGui.QIcon(':/plugins/dataset_qa_workbench/clipboard-check-solid.svg')


class ReportMailerAlgorithm(BaseAlgorithm):
    INPUT_REPORT = 'INPUT_REPORT'
    INPUT_SENDER_ADDRESS = 'INPUT_SENDER_ADDRESS'

    def initAlgorithm(
            self,
            configuration,
            p_str=None,
            Any=None,
            *args,
            **kwargs
    ):
        self.addParameter(
            QgsProcessingParameterString(
                self.INPUT_REPORT,
                self.tr('Input validation report'),
                defaultValue='{}',
                multiLine=True
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_SENDER_ADDRESS,
                self.tr('Input validation report'),
                defaultValue='@dataset_qa_workbench_sender_address',
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        raw_report = self.parameterAsString(
            parameters, self.INPUT_REPORT, context)
        report = json.loads(raw_report)
        sender_address = self.parameterAsExpression(
            parameters, self.INPUT_SENDER_ADDRESS)
        mail_message = EmailMessage()
        mail_message.set_content(raw_report)
        mail_message['Subject'] = (
            'QGIS Dataset QA Workbench plugin - Validation report')
        mail_message['From'] = sender_address
        mail_message['To'] = sender_address

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'reportmailer'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Report mailer')

    def createInstance(self):
        return ReportMailerAlgorithm()


class CrsCheckerAlgorithm(BaseAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_CRS = 'INPUT_CRS'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterMapLayer(
                self.INPUT_LAYER,
                self.tr('Input layer'),
            )
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.INPUT_CRS,
                self.tr('Input CRS')
            )
        )
        self.addOutput(
            QgsProcessingOutputBoolean(
                self.OUTPUT,
                self.tr('result')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        layer = self.parameterAsLayer(parameters, self.INPUT_LAYER, context)
        target_crs = self.parameterAsCrs(parameters, self.INPUT_CRS, context)
        layer_crs = layer.crs()
        result = layer_crs.postgisSrid() == target_crs.postgisSrid()
        return {
            self.OUTPUT: result
        }

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'crschecker'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Crs checker')

    def createInstance(self):
        return CrsCheckerAlgorithm()
