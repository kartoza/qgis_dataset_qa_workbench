import typing

from qgis.core import QgsProcessingProvider
from PyQt5 import QtGui

from . import algorithms


class DatasetQaWorkbenchProvider(QgsProcessingProvider):
    IDENTIFIER: str = 'dataset_qa_workbench'

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(algorithms.CrsCheckerAlgorithm())

    def id(self):
        return self.IDENTIFIER

    def name(self):
        return self.IDENTIFIER.replace('_', ' ').capitalize()

    def icon(self):
        return QtGui.QIcon(':/plugins/dataset_qa_workbench/clipboard-check-solid.svg')

