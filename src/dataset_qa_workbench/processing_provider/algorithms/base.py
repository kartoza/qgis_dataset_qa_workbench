import typing

from PyQt5 import (
    QtCore,
    QtGui,
)
from qgis.core import (
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsProcessingAlgorithm,
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
        return QtGui.QIcon(
            ':/plugins/dataset_qa_workbench/clipboard-check-solid.svg')


def parse_as_expression(
        raw_expression: str,
        context: typing.Optional[QgsExpressionContext] = None,
        default: typing.Optional[typing.Any] = None
):
    expression = QgsExpression(raw_expression)
    if expression.hasParserError():
        raise RuntimeError(
            f'Encountered error while parsing {raw_expression!r}: '
            f'{expression.parserErrorString()}'
        )
    if context is None:
        ctx = QgsExpressionContext()
        ctx.appendScope(QgsExpressionContextUtils.globalScope())
    else:
        ctx = context
    result = expression.evaluate(ctx)
    if expression.hasEvalError():
        raise ValueError(
            f'Encountered error while evaluating {raw_expression!r}: '
            f'{expression.evalErrorString()}'
        )
    return result if result is not None else default
