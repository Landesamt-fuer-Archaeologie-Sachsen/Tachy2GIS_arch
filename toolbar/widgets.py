import logging
import os.path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt import uic
from qgis.core import Qgis
from qgis.utils import iface

from ..common.utils import any2bool
from ..settings import LANDINGPAGE, PLUGIN_PACKAGE

LOGGER = logging.getLogger(__name__)
FORMS_DIR = os.path.join(os.path.dirname(__file__), "forms")


def _about_html(version_line, landingpage):
    return (
        f"{version_line}"
        "<p>Tachy2GIS_arch ist eine auf dem Plugin Tachy2GIS aufbauende Fachschale f&uuml;r die "
        "tachymetrische Dokumentation auf arch&auml;ologischen Ausgrabungen. "
        "Es integriert <a href=\"https://github.com/chris-jan-trapp/Tachy2GIS\">Tachy2GIS</a> "
        "sowie die Funktionalit&auml;t des Plugins "
        "<a href=\"https://github.com/ISAAKiel/profileAAR\">ProfileAAR</a>.</p>"
        "<p>Das Plugin setzt Mindestanforderungen an die verwendete Datenstruktur der Vektorlayer "
        "sowie die Verwendung von Wertelisten voraus. Details dazu finden sich in der "
        "Dokumentation unter: (Link wird noch eingef&uuml;gt).</p>"
        f"<p>Weitere Informationen und Links finden sich unter: "
        f"<a href=\"{landingpage}\">{landingpage}</a></p>"
        "<hr>"
        "<p><b>Lizenzhinweis:</b> Dieses Plugin wird unter der GNU General Public License "
        "Version 3 (GPL-3.0) ver&ouml;ffentlicht. Sie d&uuml;rfen die Software gem&auml;&szlig; "
        "den Bedingungen dieser Lizenz verwenden, ver&auml;ndern und weitergeben. "
        "Eine Kopie der Lizenz ist unter "
        "<a href=\"https://www.gnu.org/licenses/gpl-3.0.de.html\">"
        "https://www.gnu.org/licenses/gpl-3.0.de.html</a> verf&uuml;gbar.</p>"
        "<p><b>Haftungsausschluss:</b> Diese Software wird ohne jegliche Garantie bereitgestellt "
        "(&quot;as is&quot;), einschlie&szlig;lich, aber nicht beschr&auml;nkt auf die implizite "
        "Garantie der Marktreife, Eignung f&uuml;r einen bestimmten Zweck oder Nichtverletzung "
        "von Rechten Dritter. Jegliche Nutzung erfolgt auf eigenes Risiko. Die Autoren "
        "&uuml;bernehmen keine Haftung f&uuml;r Sch&auml;den oder Datenverluste, die direkt "
        "oder indirekt aus der Verwendung dieses Plugins entstehen. "
        "This Software is provided &quot;as is&quot;, without warranty of any kind.</p>"
    )


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(FORMS_DIR, "about.ui"), self)
        version_line = ""
        metadata = iface.pluginManagerInterface().pluginMetadata(PLUGIN_PACKAGE)
        if metadata:
            qgis_version = ".".join(Qgis.QGIS_VERSION.split(".")[:2])
            version_line = (
                f"<p><b>{metadata['name']}</b> "
                f"V{metadata['version_installed']} f&uuml;r QGIS {qgis_version}</p>"
            )
        self.textBrowser.setHtml(_about_html(version_line, LANDINGPAGE))
        self.textBrowser.setOpenLinks(False)
        self.textBrowser.anchorClicked.connect(QDesktopServices.openUrl)
        self.buttonClose.clicked.connect(self.accept)


class DlgSettings(QDialog):
    def __init__(self, config, autosave_manager):
        super().__init__()
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "forms", "dlgSettings.ui"), self)
        self.__config = config
        self.__autosave_manager = autosave_manager
        self.ui.treeWidget.itemClicked.connect(self.on_itemClicked)
        self.ui.butOK.clicked.connect(self.ok)
        self.ui.butAbruch.clicked.connect(self.abbruch)
        # self.ui.setup()  # extra call; constructor is not allowed to fail

    def setup(self):
        # Alle Tabs Sichtbarkeit aus
        for index in range(self.ui.tabWidget.count()):
            self.ui.tabWidget.setTabVisible(index, False)
        # Hide menu entries that are not yet implemented
        self.ui.treeWidget.topLevelItem(3).setHidden(True)  # Grabungsfotos
        self.ui.treeWidget.topLevelItem(4).setHidden(True)  # Projekt
        self.ui.treeWidget.topLevelItem(6).setHidden(True)  # Listenausgabe
        # QgsMessageLog.logMessage("setup", "T2G Archäologie", Qgis.Info)
        # Config lesen
        val = self.__config.getValue("AutoSave", "interval_in_min", "15")
        self.ui.spb_autoSaveTime.setValue(int(val))
        val = self.__config.getValue("AutoSave", "keep_last_n_backups", "10")
        self.ui.spb_keep_last_n_backups.setValue(int(val))
        val = self.__config.getValue("AutoSave", "enabled", "True")
        self.ui.chbautoSave.setChecked(any2bool(val))
        val = self.__config.getValue("Textgröße", "value", "0.70")
        self.ui.spbTextGr.setValue(float(val))
        # Punktexportpfad
        val = self.__config.getValue("Punkte Export", "pfad Exportordner", "./../Jobs")
        self.ui.txtPointPfadExp.setText(val)
        # Punktimportpfad
        val = self.__config.getValue("Punkte Import", "pfad Importordner", "./../Jobs")
        self.ui.txtPointPfadImp.setText(val)
        # Profilentzerrpunkteexport
        val = self.__config.getValue("Profilentzerrung", "pfad Exportordner", "./../Jobs")
        self.ui.txtProfilFEPPfadExp.setText(val)
        val = self.__config.getValue("Profilentzerrung", "feldNProfNr", "prof_nr")
        self.ui.txtfeldNProfNr.setText(val)
        val = self.__config.getValue("Profilentzerrung", "feldNFEP", "obj_typ")
        self.ui.txtFeldNFEP.setText(val)
        val = self.__config.getValue("Profilentzerrung", "attFEP", "Fotoentzerrpunkt")
        self.ui.txtAttFEP.setText(val)
        # MouseInfo
        val = self.__config.getValue("MouseInfo", "anzeigen", "True")
        self.ui.chbMInfo_1.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "beiBeginn", "True")
        self.ui.chbMInfo_2.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "immer", "True")
        self.ui.chbMInfo_3.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "geometrieart", "True")
        self.ui.chbMInfo_4.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "objekttyp", "True")
        self.ui.chbMInfo_5.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "objektart", "True")
        self.ui.chbMInfo_6.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "schnitt", "True")
        self.ui.chbMInfo_7.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "planum", "True")
        self.ui.chbMInfo_8.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "befund", "True")
        self.ui.chbMInfo_9.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "fund", "True")
        self.ui.chbMInfo_10.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "profil", "True")
        self.ui.chbMInfo_11.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "probe", "True")
        self.ui.chbMInfo_12.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "punktNr", "True")
        self.ui.chbMInfo_13.setChecked(any2bool(val))
        val = self.__config.getValue("MouseInfo", "koordinaten", "True")
        self.ui.chbMInfo_14.setChecked(any2bool(val))

    def ok(self):
        """Werte in Configparser eintragen"""
        self.__config.updateValue(
            "AutoSave", "enabled", "True" if self.ui.chbautoSave.checkState() == Qt.Checked else "False"
        )
        self.__config.updateValue("AutoSave", "interval_in_min", str(self.ui.spb_autoSaveTime.value()))
        self.__config.updateValue("AutoSave", "keep_last_n_backups", str(self.ui.spb_keep_last_n_backups.value()))
        self.__config.updateValue("Textgröße", "value", str(self.ui.spbTextGr.value()))
        self.__config.updateValue("Punkte Export", "pfad Exportordner", self.ui.txtPointPfadExp.text())
        self.__config.updateValue("Punkte Import", "Pfad Importordner", self.ui.txtPointPfadImp.text())
        self.__config.updateValue("Profilentzerrung", "pfad Exportordner", self.ui.txtProfilFEPPfadExp.text())
        self.__config.updateValue("Profilentzerrung", "feldNProfNr", self.ui.txtfeldNProfNr.text())
        self.__config.updateValue("Profilentzerrung", "feldNFEP", self.ui.txtFeldNFEP.text())
        self.__config.updateValue("Profilentzerrung", "attFEP", self.ui.txtAttFEP.text())
        # mouseInfo
        self.__config.updateValue("MouseInfo", "anzeigen", str(self.ui.chbMInfo_1.checkState()))
        self.__config.updateValue("MouseInfo", "beiBeginn", str(self.ui.chbMInfo_2.checkState()))
        self.__config.updateValue("MouseInfo", "immer", str(self.ui.chbMInfo_3.checkState()))
        self.__config.updateValue("MouseInfo", "geometrieart", str(self.ui.chbMInfo_4.checkState()))
        self.__config.updateValue("MouseInfo", "objekttyp", str(self.ui.chbMInfo_5.checkState()))
        self.__config.updateValue("MouseInfo", "objektart", str(self.ui.chbMInfo_6.checkState()))
        self.__config.updateValue("MouseInfo", "schnitt", str(self.ui.chbMInfo_7.checkState()))
        self.__config.updateValue("MouseInfo", "planum", str(self.ui.chbMInfo_8.checkState()))
        self.__config.updateValue("MouseInfo", "befund", str(self.ui.chbMInfo_9.checkState()))
        self.__config.updateValue("MouseInfo", "fund", str(self.ui.chbMInfo_10.checkState()))
        self.__config.updateValue("MouseInfo", "profil", str(self.ui.chbMInfo_11.checkState()))
        self.__config.updateValue("MouseInfo", "probe", str(self.ui.chbMInfo_12.checkState()))
        self.__config.updateValue("MouseInfo", "punktNr", str(self.ui.chbMInfo_13.checkState()))
        self.__config.updateValue("MouseInfo", "koordinaten", str(self.ui.chbMInfo_14.checkState()))

        self.ui.close()
        self.__config.saveFile()
        self.__autosave_manager.setup()

    def abbruch(self):
        self.ui.close()
        pass

    def on_itemClicked(self, item, column):
        """TreeViewClick zeigt Tab"""
        # title = str(item.text(column))
        self.ui.tabWidget.setCurrentIndex(self.ui.treeWidget.indexOfTopLevelItem(item))
        for index in range(self.ui.tabWidget.count()):
            if index != self.ui.treeWidget.indexOfTopLevelItem(item):
                self.ui.tabWidget.setTabVisible(index, False)
            else:
                self.ui.tabWidget.setTabVisible(index, True)
