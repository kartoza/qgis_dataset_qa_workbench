from xml.etree import ElementTree as etree

from qgis.core import (
    QgsProcessingOutputBoolean,
    QgsProcessingParameterFile,
    QgsProcessingParameterMatrix,
)

from .base import BaseAlgorithm


class XmlCheckerAlgorithm(BaseAlgorithm):
    INPUT = 'INPUT'
    INPUT_XPATH_EXPRESSIONS = 'INPUT_XPATH_EXPRESSIONS'
    OUTPUT = 'OUTPUT'

    def name(self):
        return 'xmlchecker'

    def displayName(self):
        return self.tr('XML checker')

    def createInstance(self):
        return self.__class__()

    def shortHelpString(self):
        return self.tr(
            "Perform validation on an XML file (such as a QGIS QML, a CSW "
            "metadata record, etc.\n\n"
            "This algorithm allows you to input a list of XPath expressions to"
            "be searched for in the file."
        )

    def initAlgorithm(self, config):

        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('Input file'),
            )
        )
        self.addParameter(
            QgsProcessingParameterMatrix(
                self.INPUT_XPATH_EXPRESSIONS,
                self.tr('Xpath expressions to check'),
                headers=['XPath expression']
            )
        )
        self.addOutput(
            QgsProcessingOutputBoolean(
                self.OUTPUT,
                self.tr('result')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        file_ = self.parameterAsFile(parameters, self.INPUT, context)
        tree = etree.parse(file_)
        root = tree.getroot()
        items_to_check = self.parameterAsMatrix(
            parameters, self.INPUT_XPATH_EXPRESSIONS, context)
        feedback.pushInfo(f'file_: {file_}')
        feedback.pushInfo(f'items_to_check: {items_to_check}')
        result = False
        for xpath in items_to_check:
            item = root.find(xpath)
            if item is None:
                feedback.reportError(f'Did not find {xpath!r}')
                break
        else:
            result = True
        return {
            self.OUTPUT: result
        }
