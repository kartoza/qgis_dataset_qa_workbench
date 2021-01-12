from qgis.core import (
    QgsProcessingOutputBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterMapLayer,
)

from .base import BaseAlgorithm


class CrsCheckerAlgorithm(BaseAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT_LAYER = "INPUT_LAYER"
    INPUT_CRS = "INPUT_CRS"

    def name(self):
        return "crschecker"

    def displayName(self):
        return self.tr("Crs checker")

    def createInstance(self):
        return CrsCheckerAlgorithm()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterMapLayer(
                self.INPUT_LAYER,
                self.tr("Input layer"),
            )
        )
        self.addParameter(
            QgsProcessingParameterCrs(self.INPUT_CRS, self.tr("Input CRS"))
        )
        self.addOutput(QgsProcessingOutputBoolean(self.OUTPUT, self.tr("result")))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        layer = self.parameterAsLayer(parameters, self.INPUT_LAYER, context)
        target_crs = self.parameterAsCrs(parameters, self.INPUT_CRS, context)
        layer_crs = layer.crs()
        result = layer_crs.postgisSrid() == target_crs.postgisSrid()
        return {self.OUTPUT: result}
