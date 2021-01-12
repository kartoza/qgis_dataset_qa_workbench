import typing

from qgis.core import QgsProcessingProvider
from PyQt5 import QtGui

from .algorithms import (
    crschecker,
    xmlchecker,
    reportmailer,
    reportposter,
)

_ALGORITHM_CLASSES = set()


class DatasetQaWorkbenchProvider(QgsProcessingProvider):
    IDENTIFIER: str = "dataset_qa_workbench"

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(crschecker.CrsCheckerAlgorithm())
        self.addAlgorithm(reportmailer.ReportMailerAlgorithm())
        self.addAlgorithm(reportposter.ReportPosterAlgorithm())
        self.addAlgorithm(xmlchecker.XmlCheckerAlgorithm())

    def id(self):
        return self.IDENTIFIER

    def name(self):
        return self.IDENTIFIER.replace("_", " ").capitalize()

    def icon(self):
        return QtGui.QIcon(":/plugins/dataset_qa_workbench/clipboard-check-solid.svg")
