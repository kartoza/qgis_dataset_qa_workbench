import typing
from xml.etree import ElementTree as etree

from qgis.core import (
    QgsProcessingOutputBoolean,
    QgsProcessingParameterFile,
    QgsProcessingParameterMatrix,
)

from .base import BaseAlgorithm


class QmlCheckerAlgorithm(BaseAlgorithm):
    INPUT = 'INPUT'
    INPUT_ITEMS_TO_CHECK = 'INPUT_ITEMS_TO_CHECK'
    OUTPUT = 'OUTPUT'

    def name(self):
        return 'qmlchecker'

    def displayName(self):
        return self.tr('QML checker')

    def createInstance(self):
        return self.__class__()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('Input style file'),
            )
        )
        self.addParameter(
            QgsProcessingParameterMatrix(
                self.INPUT_ITEMS_TO_CHECK,
                self.tr('Input items to check'),
                headers=['XPath']
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

        file_ = self.parameterAsFile(parameters, self.INPUT, context)
        tree = etree.parse(file_)
        root = tree.getroot()
        items_to_check = self.parameterAsMatrix(
            parameters, self.INPUT_ITEMS_TO_CHECK, context)
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


def _build_items_to_check(
        raw_items: typing.List[str]
) -> typing.Dict[str, str]:
    result = {}
    for xpath, expected in zip(raw_items[::2], raw_items[1::2]):
        result[xpath] = expected
    return result