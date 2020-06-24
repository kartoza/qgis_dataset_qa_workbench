from PyQt5 import QtCore
from qgis.core import (
    QgsFeatureSink,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingOutputBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterMapLayer,
)


class CrsCheckerAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT_LAYER = 'INPUT LAYER'
    INPUT_CRS = 'INPUT CRS'

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
                self.INPUT_CRS
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

    def createInstance(self):
        return CrsCheckerAlgorithm()
