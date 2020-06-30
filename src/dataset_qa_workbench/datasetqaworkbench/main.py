import os.path

from qgis.core import QgsApplication
from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

from ..processing_provider.provider import DatasetQaWorkbenchProvider
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .dataset_qa_workbench_dock import DatasetQaWorkbenchDock
from .utils import log_message


class DatasetQaWorkbench:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DatasetQaWorkbench_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Dataset QA Workbench')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.plugin_is_active = False
        self.dock_widget = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DatasetQaWorkbench', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        togglable=False,
        parent=None
    ):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        if togglable:
            action.setCheckable(True)
            action.toggled.connect(callback)
        else:
            action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initProcessing(self):
        self.processing_provider = DatasetQaWorkbenchProvider()
        processing_registry = QgsApplication.processingRegistry()
        processing_registry.addProvider(self.processing_provider)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        log_message('inside initGui...')
        self.initProcessing()
        icon_path = ':/plugins/dataset_qa_workbench/clipboard-check-solid.svg'
        self.add_action(
            icon_path,
            text=self.tr(u'Dataset QA Workbench'),
            callback=self.run,
            togglable=True,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def on_close_plugin(self):
        self.dock_widget.closingPlugin.disconnect(self.onClosePlugin)
        self.plugin_is_active = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        processing_registry = QgsApplication.processingRegistry()
        processing_registry.removeProvider(self.processing_provider)
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Dataset QA Workbench'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self, checked: bool):
        """Run method that performs all the real work"""

        log_message(f'inside run method - checked: {checked}')
        if checked:
            self.plugin_is_active = True
            if self.dock_widget is None:
                self.dock_widget = DatasetQaWorkbenchDock(self.iface)
            self.dock_widget.closingPlugin.connect(self.on_close_plugin)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
            self.dock_widget.show()
        else:
            self.dock_widget.hide()
