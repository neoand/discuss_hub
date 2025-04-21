import logging
import os

_logger = logging.getLogger(__name__)


class PluginBase:
    """Base class for all plugins.
    create a basic class that will be inherited by other classes
    this be initiated with a connector object, and based on the type of the connector
    it will load the approriate plugin with the same name in this folder
    """

    plugin_name = os.path.basename(__file__).split(".")[0]

    def __str__(self):
        return f"<EvoodooPlugin: {self.plugin_name}: {self.connector}>"

    def __init__(self, connector):
        self.connector = connector
        _logger.debug(
            f"Loaded plugin {self.plugin_name} for connector: {self.connector}"
        )

    def _get_status(self):
        return {
            "sucess": True,
            "plugin_name": self.plugin_name,
            "connector": str(self.connector),
            "status": "not_found",
            "qr_code_base64": None,
        }
