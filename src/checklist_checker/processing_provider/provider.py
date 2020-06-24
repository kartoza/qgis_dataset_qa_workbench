import typing

from qgis.core import QgsProcessingProvider

from . import algorithms


class ChecklistCheckerProvider(QgsProcessingProvider):
    IDENTIFIER: str = 'checklist_checker'

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(algorithms.CrsCheckerAlgorithm())

    def id(self):
        return self.IDENTIFIER

    def name(self):
        return self.IDENTIFIER.replace('_', ' ').capitalize()

    def icon(self):
        return super().icon()

