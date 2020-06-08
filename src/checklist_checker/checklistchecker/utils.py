import qgis.core

def log_message(message, level=None):
    qgis.core.QgsMessageLog.logMessage(message)
