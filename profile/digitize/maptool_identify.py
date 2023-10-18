import time

from qgis.gui import QgsMapToolIdentify, QgsAttributeDialog, QgsAttributeEditorContext

from ..publisher import Publisher
from .maptool_mixin import MapToolMixin

## @brief With the MapToolIdentify class a map tool for identify feature attributes is realized
#
# The class inherits form QgsMapToolIdentify and MapToolMixin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2022-28-09


class MapToolIdentify(QgsMapToolIdentify, MapToolMixin):
    def __init__(self, canvas, iFace):
        self.lastLinkObj = None
        self.__iface = iFace
        self.pup = Publisher()
        self.canvas = canvas
        self.digiPointLayer = None
        self.digiLineLayer = None
        self.digiPolygonLayer = None
        QgsMapToolIdentify.__init__(self, self.canvas)
        self.featForm = None
        self.lastMapCoord = None
        self.time_function_done = time.time()

    ## \brief Takes the press event of the canvas
    #
    #
    # Identify features and displays the related attributes in a QgsAttributeDialog
    #
    def canvasPressEvent(self, event):
        results = self.identify(
            event.x(),
            event.y(),
            [self.digiPointLayer, self.digiLineLayer, self.digiPolygonLayer],
            QgsMapToolIdentify.TopDownAll,
        )
        for i in range(len(results)):
            if isinstance(self.featForm, QgsAttributeDialog):
                self.featForm.close()
            self.featForm = QgsAttributeDialog(
                vl=results[i].mLayer,
                thepFeature=results[i].mFeature,
                parent=self.canvas,
                featureOwner=False,
                showDialogButtons=False,
                context=QgsAttributeEditorContext(),
            )
            self.featForm.closeEvent = self.close_form
            self.featForm.setWindowTitle("Feature Eigenschaften")
            self.featForm.show()

            self.pup.publish("removeHoverFeatures", {})

            linkObj = {"layer": results[i].mLayer, "features": [results[i].mFeature]}
            self.pup.publish("addHoverFeatures", linkObj)

    def close_form(self, event):
        self.pup.publish("removeHoverFeatures", {})

    def setDigiPointLayer(self, digiPointLayer):
        self.digiPointLayer = digiPointLayer

    def setDigiLineLayer(self, digiLineLayer):
        self.digiLineLayer = digiLineLayer

    def setDigiPolygonLayer(self, digiPolygonLayer):
        self.digiPolygonLayer = digiPolygonLayer

    def canvasMoveEvent(self, e):
        self.lastMapCoord = e.pos()
        self.handleMove()

    def handleMove(self):
        if (self.time_function_done + 0.1) > time.time():
            return
        self.time_function_done = time.time()

        results = self.identify(
            self.lastMapCoord.x(),
            self.lastMapCoord.y(),
            [self.digiPointLayer, self.digiLineLayer, self.digiPolygonLayer],
            # [self.digiPolygonLayer],
        )

        if len(results) == 0:
            self.pup.publish("removeHoverFeatures", {})
        if len(results) > 0:
            linkObj = {"layer": results[0].mLayer, "features": [results[0].mFeature]}
            if linkObj != self.lastLinkObj:
                self.lastLinkObj = linkObj
                self.pup.publish("removeHoverFeatures", {})
                self.pup.publish("addHoverFeatures", linkObj)

        # print(self.lastMapCoord.x(), self.lastMapCoord.y(), results)
