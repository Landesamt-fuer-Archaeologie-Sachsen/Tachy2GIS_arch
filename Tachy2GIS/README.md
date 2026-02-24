**Dependencies:** The Tachy2GIS 3D-Viewer requires vtk to run. If you don't have it already (test this by typing `import vtk` in a python console), see **Installation**. Alternatively you can use pipenv to handle the dependencies for you, see the section **Developer Notes** further down for more info on this.* Note that the python vtk library only provides a wrapper around the actual vtk installation Also required is [tachyconnect](https://github.com/gbv/tachyconnect), which will handle the connection to the total station. It can be installed via pip.

*You need at least QGIS version 3.10.7. This is because there are issues in previous versions when creating geometry from Well-known text. Your Total Stations **Data Output** setting has to be set to `Interface` and the **GSI Mask** setting has to be set to `Mask2` to be able to read coordinates from GSI. To use Bluetooth, you need a Bluetooth driver like `Bluetooth Stack for Windows by Toshiba` that merges the input and output COM port into one.*

**Restrictions:**
*Tachy2GIS is at this moment restricted to Leica Totalstations and the Leica GSI 8/16 data format for measurements triggered at the total station. Remote triggering, Reading and setting the reflector height and robotic functions assume that the geoCOM 1100 dialect is understood. 

**Known Issues:** Points don't get rendered on certain integrated graphics cards. This can be fixed by removing all lines with RenderPointsAsSpheresOn() in `visualization.py`. Points will then be displayed as squares.

**Funding:** *Free software isn't necessarily produced for free. The development of Tachy2GIS has been funded by the [Archeological Museum of Hamburg](https://amh.de/), the [Lower Saxony Institute for Historical Coastal Research](https://nihk.de/) and the [German Archeological Institute](https://www.dainst.org/). If you want to get into the boat, feel free to contact us.*

## Installation

#### Windows

First, you have to install [vtk](https://vtk.org/).
The best way to do this is via pip invoked from the OSGEO4W shell:

`python -m pip install vtk` 

After that, you can install [tachyconnect](https://pypi.org/project/tachyconnect/):

`python -m pip install tachyconnect` 

With the requirements met you can install Tachy2GIS from the plugin manager. Make sure to activate the support of experimental plugins. Alternatively you can either install Tachy2GIS 3D-Viewer directly from zip in QGIS, or unpack it into your QGIS Plugins folder (QGIS restart required): `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins`

# Tachy2GIS: Concepts and Architecture

Tachy2GIS (henceforth 'T2G') enables you to create geometries directly from tachymeter input while at the same time adding vertices manually. Manually generated vertices snap to features that are already present, in order to avoid overlapping features or holes between directly adjacent geometries. T2G consists of four main elements:

*   The main dialog window which allows to connect to a tachymeter, preview vertices that are generated and select the source layer
*   The field dialog that allows editing of the attribute values of new geometries and the selection of the target layer. The concept of source- and target layer will be explained later
*   The vertex picker map tool, that is used to add existing vertices to a new geometry by clicking on or near them
*   The vertex list that works behind the scenes to make all the above possible. It handles vertex snapping, displaying of current vertices and export of geometries.

## Source- and target layer

The source layer is the layer that provides the vertices for snapping, e.g. existing geometries. It is scanned for vertices every time it changes. This process may take some time, ranging from fractions of a second for layers with few simple geometries (a hundred polygons or less) to several minutes for layers with thousands of complex shapes. Scanning invokes a progress dialog and can be aborted if started on a layer that takes too long to load. This will however mean that you will not be able to snap to the geometries in this layer.

The target layer is the one that new geometries will be added to. Its geometry type determines the appearance of the map tool -> if the target layer holds polygons, the map tool will draw polies, a point target will show up as simple vertices when adding geometries.

*Note:* Source- and target layer may (and will likely) be identical. They only play different roles in the process. If source and target are identical, all geometries that exist before the one that is being added are available for snapping.

Both layers have to be vector layers. They do _not_ have to be of the same geometry type though, meaning it is possible to create a polygon target layer that is anchored to reference points in a point source layer.

## The main dialog

The main dialog window consists of a tool bar and a 3D map window. All icons used here are emoji because we are too lazy to compile icons. The toolbar gives you:

* A camera reset button 🎦
* A combobox that allows you to adjust the automatic zoom from off via active layer to up to last eight new features.
* Two more comboboxes for source- and target layer.
* The unicorn button that 🦄 will magically close a segment when tracing existing geometries. To do this, the last three traced vertices will be used as starting point, one on the way and end point of the new segment. The one on the way is required to define the direction (clockwise or counterclockwise) of the traced segment.
* The 'create geometry' button labeled with a checkmark: ✔️. When you are happy with your new vertices you click here and are confronted with the properties dialog.
* The 'delete last vertex' button (❌), which does just that.
* The 'trigger measurement' button which with some fonts looks like a laser symbol (🎇). In others it is just sparkly.
* Then comes a text box that either shows the last created vertex or the result of the last measurement. This depends on the capabilities of the used instrument and may well be an error message. "`Not implemented yet.`" and "`Unknown RPC, procedure ID invalid`" are two examples that you may expect from devices that do not offer the required functionality.
* The next button (📜) lets you select a log file into which incoming measurements will be dumped. Once selected the path will be displayed as tool tip. The file does not have to exist when opening and incoming measurements will always be appended.
* When connected to a device that lets you set the reflector height, you get a text box that displays the currently set ref_z and will transmit a value entered here.
* The joystick button (🕹) opens a dialog that allows controlling a total station with robotic functionality.
* The cloud button (⛅) lets you load a point cloud (so far only ascii) as a source layer. This is useful for tracing profiles.
* The rightmost button is the connect button which also displays the state of the connection to the tachymeter:
  * ⚠️ indicates that no serial device and thus no total station has been detected.
  * 🔌 indicates that a serial port is available but not connected. Click to change that. This sends a geoCOM command to each detected serial device and assumes that the first that responds with a valid geoCOM reply is a total station.This WILL break when you have more than one geoCOM capable device connected to your system.
  * 🔗 signifies an established connection


## Hotkeys

- `ctrl-Space`: Triggers a measurement.
- `ctrl-alt-Return`: Dumps the current geometry and opens the attribute dialog
- `ctrl-alt-Z`: Deletes the last added vertex
- `ctrl-alt-J`: Opens the joystick interface:
  - ⬆️⬇️⬅️➡️ are linked to the arrow keys
  - Stop (🛑) is `space`
  - Lock is `ctrl-alt-L`
  - powersearch (🤖) is connected to `ctrl-alt-S`
  - The window can be closed with `Return`


## Connecting a tachymeter

The tachymeter connection is implemented as a polling background thread that is provided by the package [tachyconnect](https://pypi.org/project/tachyconnect/). 

Make sure that your tachymeter is set to the same crs as your target layer. Currently there is no way to tell which format is used, so better be careful.

## Creating new geometries and setting their attributes

Geometries are created by sending measurements from the tachymeter or by adding vertices manually. Once all vertices are created, they are written to the target layer by clicking the '✔️' button next to the vertex line edit. This opens the 'Attribute Dialog' where you can input the attribute values of the new feature. If there already are features present in the target layer, the values of the most recent feature are used as default values for the new one. 


## Developer Notes

To provide a consistent working environment that only minimally messes up your python installation, T2G now comes with a [Pipfile](https://github.com/pypa/pipenv) that keeps track of dependencies.  to use this, first create an environment by calling

`$ pipenv --three --site-packages`

and then install all packages with

`$ pipenv install`

The `--site-packages` flag is required to integrate everything else that's required by QGIS into the virtual environment. You can now start QGIS from a pipenv shell:

```
$ pipenv shell
$ qgis &
```

Please note that the 3D-viewer depends on vtk. Please install vtk via pip if you want to use the 3D-viewer plugin.

