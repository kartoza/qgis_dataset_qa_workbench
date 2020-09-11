import typing
from pathlib import Path
from sys import getfilesystemencoding

import qgis.core
from qgis.core import QgsExpressionContextUtils
from PyQt5 import (
    QtCore,
    QtGui,
)
from PyQt5.QtCore import QAbstractItemModel

from .constants import DatasetType


def log_message(message, level=None):
    qgis.core.QgsMessageLog.logMessage(message)


def get_qgis_variable(
        name: str,
        fallback_name: typing.Optional[str] = None
) -> typing.Optional[str]:
    global_scope = QgsExpressionContextUtils.globalScope()
    value = global_scope.variable(name)
    if value is not None:
        result = value
    elif fallback_name is not None:
        result = global_scope.variable(fallback_name)
    else:
        result = value
    return result


def get_checklists_dir() -> Path:
    base_dir = get_profile_base_path()
    checklists_dir = base_dir / 'checklists'
    if not checklists_dir.is_dir():
        log_message(f'Creating checklists directory at {checklists_dir}...')
        checklists_dir.mkdir(parents=True, exist_ok=True)
    return checklists_dir


def get_profile_base_path() -> Path:
    return Path(qgis.core.QgsApplication.qgisSettingsDirPath())


def match_maplayer_type(type_: qgis.core.QgsMapLayerType) -> typing.Optional[DatasetType]:
    return {
        qgis.core.QgsMapLayerType.VectorLayer: DatasetType.VECTOR,
        qgis.core.QgsMapLayerType.RasterLayer: DatasetType.RASTER,
    }.get(type_)


class TreeNode:

    def __init__(self, parent, row):
        self.parent = parent
        self.row = row
        self.sub_nodes = self._get_children()

    def _get_children(self):
        raise NotImplementedError


class TreeModel(QAbstractItemModel):

    def __init__(self):
        super().__init__()
        self.root_nodes = self._get_root_nodes()

    def _get_root_nodes(self):
        raise NotImplementedError

    def index(self, row: int, column: int, parent: typing.Optional[QtCore.QModelIndex] = QtCore.QModelIndex()):
        if not parent.isValid():
            result = self.createIndex(row, column, self.root_nodes[row])
        else:
            parent_node: TreeNode = parent.internalPointer()
            result = self.createIndex(row, column, parent_node.sub_nodes[row])
        return result

    def parent(self, index: QtCore.QModelIndex):
        if not index.isValid():
            result = QtCore.QModelIndex()
        else:
            node: TreeNode = index.internalPointer()
            if node.parent is None:
                result = QtCore.QModelIndex()
            else:
                result = self.createIndex(node.parent.row, 0, node.parent)
        return result

    def reset(self):
        self.root_nodes = self._get_root_nodes()
        super().reset()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if not parent.isValid():
            result = len(self.root_nodes)
        else:
            node: TreeNode = parent.internalPointer()
            result = len(node.sub_nodes)
        return result


def serialize_report_to_plain_text(report: typing.Dict) -> str:
    validation_check_template_path = (
        ':/plugins/dataset_qa_workbench/validation-report-check-template.txt')
    check_template_fh = QtCore.QFile(validation_check_template_path)
    check_template_fh.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text)
    check_template = check_template_fh.readAll().data().decode(
        getfilesystemencoding())
    check_template_fh.close()
    rendered_checks = []
    log_message('Rendering checks...')
    for check in report.get('checks', []):
        rendered = check_template.format(
            check_name=check['name'],
            validated='YES' if check['validated'] else 'NO',
            description=check['description'],
            notes=check['notes'].replace('{', '{{').replace('}', '}}'),
        )
        log_message(f'check {rendered}')
        rendered_checks.append(rendered)
    log_message('Rendering final report...')
    validation_report_template_path = (
        ':/plugins/dataset_qa_workbench/validation-report-template.txt')
    report_template_fh = QtCore.QFile(validation_report_template_path)
    report_template_fh.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text)
    report_template = report_template_fh.readAll().data().decode(
        getfilesystemencoding())
    report_template_fh.close()
    ready_to_render = report_template.replace(
        '{checks}', '\n'.join(rendered_checks))
    log_message(f'Replaced checks placeholder: {report_template}')
    rendered_report = ready_to_render.format(
        checklist_name=report['checklist'],
        dataset_name=report['dataset'],
        timestamp=report['generated'],
        result=report['dataset_is_valid'],
        author=report['validator'],
        description=report['description'],
    )
    return rendered_report


def serialize_report_to_html(report: typing.Dict) -> QtGui.QTextDocument:
    validation_check_template_path = (
        ':/plugins/dataset_qa_workbench/validation-report-check-template.html')
    check_template_fh = QtCore.QFile(validation_check_template_path)
    check_template_fh.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text)
    check_template = check_template_fh.readAll().data().decode(
        getfilesystemencoding())
    check_template_fh.close()
    rendered_checks = []
    log_message('Rendering checks...')
    for check in report.get('checks', []):
        rendered = check_template.format(
            check_name=check['name'],
            validated='YES' if check['validated'] else 'NO',
            description=check['description'],
            notes=check['notes'].replace('{', '{{').replace('}', '}}'),
        )
        log_message(f'check {rendered}')
        rendered_checks.append(rendered)
    log_message('Rendering final report...')
    validation_report_template_path = (
        ':/plugins/dataset_qa_workbench/validation-report-template.html')
    report_template_fh = QtCore.QFile(validation_report_template_path)
    report_template_fh.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text)
    report_template = report_template_fh.readAll().data().decode(
        getfilesystemencoding())
    report_template_fh.close()
    ready_to_render = report_template.replace(
        '{checks}', '\n'.join(rendered_checks))
    log_message(f'Replaced checks placeholder: {report_template}')
    rendered_report = ready_to_render.format(
        checklist_name=report['checklist'],
        dataset_name=report['dataset'],
        timestamp=report['generated'],
        result=report['dataset_is_valid'],
        author=report['validator'],
        description=report['description'],
    )
    doc = QtGui.QTextDocument()
    doc.setHtml(rendered_report)
    return doc
