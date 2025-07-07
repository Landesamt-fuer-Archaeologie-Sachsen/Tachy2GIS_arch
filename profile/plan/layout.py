import os
from qgis.core import QgsProject, QgsMapSettings, QgsRectangle, QgsRasterLayer, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutPoint, QgsLayoutSize, QgsUnitTypes, QgsLayoutItemLabel,QgsLayoutItemLegend, QgsLayoutExporter
from PyQt5.QtGui import QColor

## @brief Layout class
#
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2022-03-15

class Layout():

    def __init__(self, iFace):

        self.__iface = iFace

        self.iconpath = os.path.join(os.path.dirname(__file__), '...', 'Icons')

        self.projectInstance = QgsProject.instance()

        self.imageLayerProfil = ''

        self.layout = ''

        self.canvasPlan = ''


    ## \brief Start lyout creation
    #
    #
    # creates a new layout
    #
    def startLayout(self, planData):
        print('start_layout_2')
        self.layout = self.__createLayout(planData['profilePath'])
        self.__exportLayout(self.layout)
    
    # remove any duplicate layouts
    def __removeDuplicateLayout(self, layoutName):
        layouts_list = self.projectInstance.layoutManager().printLayouts()        
        for layout in layouts_list:
            if layout.name() == layoutName:
                self.projectInstance.layoutManager().removeLayout(layout)

    def __createImageLayer(self, profilePath):
        self.imageLayerProfil = QgsRasterLayer(profilePath, "Profile image")
        if not self.imageLayerProfil.isValid():
            print("imageLayerProfil failed to load!")

        self.projectInstance.addMapLayer(self.imageLayerProfil)

    def __removeImageLayer(self):
        self.projectInstance.removeMapLayer(self.imageLayerProfil)

    def __createLayout(self, profilePath):
        #Init layout
        layoutName = "LfA Testlayout"
        self.__removeDuplicateLayout(layoutName)
        lyt = QgsPrintLayout(self.projectInstance)
        lyt.initializeDefaults()
        lyt.setName(layoutName)
        self.projectInstance.layoutManager().addLayout(lyt)

        #Init map item
        map = QgsLayoutItemMap(lyt)
        map.setRect(20, 20, 20, 20)

        #Layers
        self.__createImageLayer(profilePath)

        layerCrs = self.imageLayerProfil.crs()

        print('layerCrs', layerCrs)
        print('imageLayerProfil', self.imageLayerProfil)

        #mapSettings = map.mapSettings()
        mapSettings = QgsMapSettings()
        
        #mapSettings.setDestinationCrs(layerCrs)
        #mapSettings.setKeepLayerSet(False)
        mapSettings.setLayers([self.imageLayerProfil]) # set layers to be mapped
        map.setLayers([self.imageLayerProfil]) # set layers to be mapped

        rect = QgsRectangle(mapSettings.fullExtent())
        rect.scale(1.0)
        mapSettings.setExtent(rect)
        map.setExtent(rect)
        
        map.setBackgroundColor(QColor(255, 150, 150, 0))

        print('layersToRender', map.layersToRender())
        lyt.addLayoutItem(map)
        #lyt.addLayoutItem(self.canvasPlan)
        

        #print('layerIds', mapSettings.layerIds())
        #print('layers', mapSettings.layers())
        
        

        #print('layerIds', mapSettings.layerIds())
        #print('layers', mapSettings.layers())

        map.attemptMove(QgsLayoutPoint(5, 20, QgsUnitTypes.LayoutMillimeters))
        map.attemptResize(QgsLayoutSize(180, 180, QgsUnitTypes.LayoutMillimeters))


        #Label
        #label = QgsLayoutItemLabel(lyt)
        #label.setText("Hello world")
        #label.adjustSizeToText()
        #lyt.addLayoutItem(label)

        #legend
        #legend = QgsLayoutItemLegend(lyt)
        #legend.setLinkedMap(map) # map is an instance of QgsLayoutItemMap
        #lyt.addLayoutItem(legend)

        return lyt

    def __exportLayout(self, layout):
        print('__exportLayout')
        base_path = os.path.join(QgsProject.instance().homePath())
        pdf_path = os.path.join(base_path, "output.pdf")

        exporter = QgsLayoutExporter(layout)
        print('pdf_path', pdf_path)
        exporter.exportToPdf(pdf_path, QgsLayoutExporter.PdfExportSettings())

        self.__removeImageLayer()


 