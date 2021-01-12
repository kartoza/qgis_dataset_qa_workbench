from qgis.core import (
    QgsGeometry,
    QgsProcessingOutputBoolean,
    QgsProcessingParameterMapLayer,
    QgsProcessingParameterExtent,
    QgsProcessingParameterEnum,
)

from . import base


class ExtentChecker(base.BaseAlgorithm):
    INPUT = "INPUT"
    INPUT_EXTENT = "INPUT_EXTENT"
    INPUT_OPERATION = "INPUT_OPERATION"
    OUTPUT = "OUTPUT"
    OPERATION_OPTIONS = [
        "intersects",
        "overlaps",
        "contains",
        "crosses",
        "disjoint",
        "touches",
        "whithin",
    ]

    def name(self):
        return "extentchecker"

    def displayName(self):
        return self.tr("Extent checker")

    def createInstance(self):
        return self.__class__()

    def shortHelpString(self):
        return self.tr(
            "Check if the input layer's extent is related to the target extent "
            "according to the specified spatial relation"
        )

    def initAlgorithm(self, config):

        self.addParameter(
            QgsProcessingParameterMapLayer(
                self.INPUT,
                self.tr("Input layer"),
            )
        )
        self.addParameter(
            QgsProcessingParameterExtent(
                self.INPUT_EXTENT,
                self.tr("Target extent to match"),
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT_OPERATION,
                self.tr("spatial operation to test"),
                self.OPERATION_OPTIONS,
                defaultValue=self.OPERATION_OPTIONS[0],
            )
        )
        self.addOutput(QgsProcessingOutputBoolean(self.OUTPUT, self.tr("result")))

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsLayer(parameters, self.INPUT, context)
        target_extent = self.parameterAsExtent(parameters, self.INPUT_EXTENT, context)
        operation_index = self.parameterAsEnum(
            parameters, self.INPUT_OPERATION, context
        )
        operation = self.OPERATION_OPTIONS[operation_index]
        feedback.pushInfo(f"layer: {layer.name()}")
        feedback.pushInfo(f"target_extent: {target_extent}")
        feedback.pushInfo(f"operation: {operation}")
        layer_geom = QgsGeometry.fromRect(layer.extent())
        target_geom = QgsGeometry.fromRect(target_extent)
        spatial_operation_method = getattr(layer_geom, operation)
        if spatial_operation_method is not None:
            result = spatial_operation_method(target_geom)
        else:
            result = False
        return {self.OUTPUT: result}
