import os

from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QApplication, QInputDialog

from qgis.core import QgsMapLayer, QgsMessageLog, Qgis, QgsCoordinateReferenceSystem, QgsProject
from qgis.utils import iface

from ...common.utils import FileFunctions, delSelectFeature
from ...settings import PLUGIN_NAME


def gtiff2jpg():
    layer = iface.mapCanvas().currentLayer()
    if layer.type() == QgsMapLayer.RasterLayer and layer.source()[-3:] == "tif":
        input_path = os.path.abspath(str(layer.source()))
        outputsrs = layer.crs().authid()
        QgsMessageLog.logMessage(input_path, PLUGIN_NAME, Qgis.Info)

        try:
            input_path = str(layer.source())

            inputtemp = input_path
            outputtemp = os.path.splitext(input_path)[0] + "_transf" + os.path.splitext(input_path)[1]

            string = (
                    r"gdal_translate -of JPEG -scale -co worldfile=yes " + '"' + inputtemp + '" "' + outputtemp + '"'
            )
            os.system(string)

            output_file = QFileDialog.getSaveFileName(
                None, "Speicherpfad", os.path.splitext(input_path)[0], "Jpeg mit World (*.jpg);;Alle (*.*)"
            )
            if output_file[0] != "":
                FileFunctions().file_copy(outputtemp, output_file[0][:-4] + ".jpg")
                FileFunctions().file_copy(outputtemp[:-4] + ".wld", output_file[0][:-4] + ".wld")

                rasterlayer = iface.addRasterLayer(
                    output_file[0][:-4] + ".jpg", os.path.basename(output_file[0])[:-4]
                )
                rasterlayer.setCrs(QgsCoordinateReferenceSystem(outputsrs))

                box = QMessageBox()
                box.setIcon(QMessageBox.Question)
                box.setWindowTitle("Frage")
                box.setText("Datei löschen?")
                box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Abort)
                buttonY = box.button(QMessageBox.Yes)
                buttonY.setText("GeoTIF")
                buttonY.setToolTip("Löscht GeoTiff und Layer")
                buttonN = box.button(QMessageBox.No)
                buttonN.setText("Layer")
                buttonN.setToolTip("Löscht denn Layer")
                buttonA = box.button(QMessageBox.Abort)
                buttonA.setText("Behalten")
                buttonA.setToolTip("Löscht keins von beiden")
                buttonA.setFocus()
                box.exec_()

                if box.clickedButton() == buttonY:
                    QgsProject.instance().removeMapLayer(layer.id())
                    a = 0
                    for layer in QgsProject.instance().mapLayers().values():
                        QgsMessageLog.logMessage(layer.source(), PLUGIN_NAME, Qgis.Info)
                        if input_path in layer.source():
                            a = a + 1
                    if a == 0:
                        FileFunctions().file_del(input_path)
                        FileFunctions().file_del(input_path[:-4] + ".wld")
                    else:
                        iface.messageBar().pushMessage(
                            PLUGIN_NAME,
                            "Datei ist mehrfach als Layer eingefügt und kann nicht gelöscht werden.",
                            level=Qgis.Critical,
                        )
                elif box.clickedButton() == buttonN:
                    QgsProject.instance().removeMapLayer(layer.id())

                elif box.clickedButton() == buttonA:
                    pass

        except Exception as e:
            QgsMessageLog.logMessage(str(e), PLUGIN_NAME, Qgis.Info)
        finally:
            FileFunctions().file_del(outputtemp)
            FileFunctions().file_del(outputtemp[:-4] + ".wld")
            FileFunctions().file_del(outputtemp[:-4] + ".tif.aux.xml")
    else:
        iface.messageBar().pushMessage(
            PLUGIN_NAME, "Layer ist kein Rasterlayer oder eine GeoTif!", level=Qgis.Critical
        )


def rasterCut():
    # Layer des zu schneidenden Bildes
    layer = iface.mapCanvas().currentLayer()

    if layer.type() != QgsMapLayer.RasterLayer:
        iface.messageBar().pushMessage(
            PLUGIN_NAME, "Layer ist kein Rasterlayer!", level=Qgis.Critical
        )
        return

    box = QMessageBox()
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle("Frage")
    box.setText("Neue Schnittmaske erstellen oder vorh. Maske verwenden.")
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    buttonY = box.button(QMessageBox.Yes)
    buttonY.setText("Neu")
    buttonY.setToolTip("Erstellt eine Schnittmaske durch zeichnen eines Polygons.")
    buttonN = box.button(QMessageBox.No)
    buttonN.setText("vorh. Maske")
    buttonN.setToolTip("Nutzt die Objekte im Layer Schnittmaske")
    box.exec_()
    # Layer mit Schnittmaske/n in Variable speichern und activ setzen
    cutlayer = QgsProject.instance().mapLayersByName("Schnittmaske")[0]
    iface.setActiveLayer(cutlayer)
    # Auswahl neue Schnittmaske
    if box.clickedButton() == buttonY:
        # Schnittmasken Layer zum editing öffnen
        cutlayer.startEditing()
        # alle Geometrien löschen
        listOfIds = [feat.id() for feat in cutlayer.getFeatures()]
        cutlayer.deleteFeatures(listOfIds)
        # Qgis Kartenfenster aktuallisieren
        iface.mapCanvas().refresh()
        # Aktion Neues Objekt auslösen
        iface.actionAddFeature().trigger()
        # Warten bis ein neues Objekt gezeichnet wurde
        while cutlayer.featureCount() < 1:
            QApplication.processEvents()
        # Änderungen übernehmen
        cutlayer.commitChanges()
    # Auswahl Vorhandene Schnittmaske
    elif box.clickedButton() == buttonN:
        if cutlayer.featureCount() == 0:
            iface.messageBar().pushMessage(
                PLUGIN_NAME, "Keine Objekte auf Maskenlayer vorhanden! Abbruch", level=Qgis.Critical
            )
            return
    else:
        # Bei keiner Auswahl Abbruch
        return
    # Layer des zu schneidenden Bildes aktiv setzen
    iface.setActiveLayer(layer)

    # Layerpfad in Variable speichern
    input_path = os.path.abspath(str(layer.source()))
    # Programmteil zum schneideen des Bildes
    try:
        # Maskenlayerpfad in Variable speichern
        masklayerpfad = str(cutlayer.source()).split("|")[0]
        masklayername = "Schnittmaske"
        # Layer Koordinatensysteme in Variable speichern
        inputsrs = layer.crs().authid()
        outputsrs = layer.crs().authid()

        temp_input_raster = None
        temp_output_raster = None
        # Pfad Eingaberaster in Variable speichern
        temp_input_raster = input_path
        # Pfad Ausgaberaster in Variable speichern
        temp_output_raster = os.path.splitext(input_path)[0] + "_cut" + os.path.splitext(input_path)[1]

        items = ("keine", "75", "50", "25")
        kompress = None
        kompressv, ok = QInputDialog.getItem(None, "Kompression", "JPEG-Qualität eingeben", items, 0, False)
        if ok != True:
            # Abbruch
            return
        else:
            # Kompressionsvariable setzen
            if kompressv == "keine":
                kompress = ""
            else:
                kompress = "-co COMPRESS=JPEG -co JPEG_QUALITY=" + kompressv
        # Gdal Komandozeile zusammensetzen
        string = (
                r"gdalwarp"
                + " -s_srs "
                + inputsrs
                + " -t_srs "
                + outputsrs
                + ' -of GTiff -cutline "'
                + masklayerpfad
                + '" -cl '
                + masklayername
                + " -crop_to_cutline -dstalpha "
                + kompress
                + ' "'
                + temp_input_raster
                + '" "'
                + temp_output_raster
                + '"'
        )
        # Komandozeile an System senden
        os.system(string)
        # Speicherdialog aufrufen
        dlg = QFileDialog()
        initFilter = ""
        if temp_input_raster[:3] == "jpg":
            initFilter = "Jpeg mit World (*.jpg)"
        elif temp_input_raster[:3] == "tif":
            initFilter = "GeoTif (*.tif)"

        output_file = dlg.getSaveFileName(
            None,
            "Speicherpfad",
            input_path,
            "GeoTif (*.tif);;Jpeg mit World (*.jpg);;Alle (*.*)",
            initialFilter=initFilter,
        )
        # Ausgewähltes Ausgabeformat auswerten
        if output_file[1] == "GeoTif (*.tif)":
            s = os.path.splitext(output_file[0])[0]
            # temp. geschnittenes Bild unter neuen Namen speichern
            FileFunctions().file_copy(temp_output_raster, s + ".tif")
            # Bild als neuen Layer einfügen
            iface.addRasterLayer(s + ".tif", os.path.basename(output_file[0])[:-4])

        elif output_file[1] == "Jpeg mit World (*.jpg)":
            s = os.path.splitext(output_file[0])[0]
            temp_input_raster = temp_output_raster
            temp_output_raster_transl = s + ".jpg"
            # Gdal Komandozeile zusammensetzen umwandlung zu Jpeg
            string = (
                    r'gdal_translate -of Jpeg -co worldfile=yes -mask 4 "'
                    + temp_input_raster
                    + '" "'
                    + temp_output_raster_transl
                    + '"'
            )
            # Komandozeile an System senden
            os.system(string)
            # Bild als neuen Layer einfügen
            rasterlayer = iface.addRasterLayer(s + ".jpg", os.path.basename(output_file[0])[:-4])
            # Layer Koordinatensystem setzen
            rasterlayer.setCrs(QgsCoordinateReferenceSystem(outputsrs))
    except Exception as e:
        QgsMessageLog.logMessage(str(e), PLUGIN_NAME, Qgis.Info)
        # temp. geschnittenes Bild löschen
        FileFunctions().file_del(temp_output_raster)
    finally:
        QgsMessageLog.logMessage("datei löschen", PLUGIN_NAME, Qgis.Info)
        # temp. geschnittenes Bild löschen
        FileFunctions().file_del(temp_output_raster)

    box = QMessageBox()
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle("Frage")
    box.setText("Ausgangsdatei löschen?")
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Abort)
    buttonY = box.button(QMessageBox.Yes)
    buttonY.setText("Datei und Layer")
    buttonY.setToolTip("Löscht Datei und Layer")
    buttonN = box.button(QMessageBox.No)
    buttonN.setText("Layer")
    buttonN.setToolTip("Löscht nur denn Layer")
    buttonA = box.button(QMessageBox.Abort)
    buttonA.setText("Behalten")
    buttonA.setToolTip("Löscht keins von beiden")
    buttonA.setFocus()
    box.exec_()

    if box.clickedButton() == buttonY:
        QgsProject.instance().removeMapLayer(layer.id())
        a = 0
        for layer in QgsProject.instance().mapLayers().values():
            QgsMessageLog.logMessage(layer.source(), PLUGIN_NAME, Qgis.Info)
            if input_path in layer.source():
                a = a + 1
        if a == 0:
            FileFunctions().file_del(input_path)
        else:
            iface.messageBar().pushMessage(
                PLUGIN_NAME,
                "Datei ist mehrfach als Layer eingefügt und kann nicht gelöscht werden.",
                level=Qgis.Critical,
            )
    elif box.clickedButton() == buttonN:
        QgsProject.instance().removeMapLayer(layer.id())
        pass
    elif box.clickedButton() == buttonA:
        pass


def setCutMask():
    cutlayer = QgsProject.instance().mapLayersByName("Schnittmaske")[0]
    actlayer = None
    for layer in QgsProject.instance().mapLayers().values():
        if layer.type() == QgsMapLayer.VectorLayer:
            if layer.selectedFeatureCount() > 0:
                actlayer = layer
                break
    if actlayer == None:
        iface.messageBar().pushMessage(
            PLUGIN_NAME, "Keine Objekte gewählt! Abbruch", level=Qgis.Critical
        )
        return
    iface.actionCopyFeatures().trigger()
    iface.setActiveLayer(cutlayer)
    cutlayer.startEditing()
    iface.actionPasteFeatures().trigger()
    cutlayer.commitChanges()
    delSelectFeature()
    iface.actionSelectRectangle().trigger()


def delCutMask():
    cutlayer = QgsProject.instance().mapLayersByName("Schnittmaske")[0]
    cutlayer.startEditing()
    listOfIds = [feat.id() for feat in cutlayer.getFeatures()]
    cutlayer.deleteFeatures(listOfIds)
    cutlayer.commitChanges()
    iface.messageBar().pushMessage(PLUGIN_NAME, "Maskenlayer gelöscht", level=Qgis.Info)



