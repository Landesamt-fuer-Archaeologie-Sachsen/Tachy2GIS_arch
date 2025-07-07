from os import listdir
from os.path import exists, abspath, join, dirname

ICON_PATHS = {
    # icons in plugin folder
    "plugin_icon": "plugin_icon.png",
    "points_import": "PunktImp.gif",
    "points_export": "PunktExp.gif",
    "points_export_profile": "ProfPunktExp.gif",
    "hourglass": "hourglass-svgrepo-com.svg",
    "free": "Frei.gif",
    "circle_2_points_radius": "Circle2PR.gif",
    "circle_2_points_diameter": "Circle2P.gif",
    "delete_vertex": "delVertex.png",
    "rectangle": "Rectangle.gif",
    "add_vertex": "addVertex.png",
    "Formular": "Formular.jpg",
    "FeatureSelect": "FeatureSelect.gif",
    "FeatureMove": "FeatureMove.gif",
    "FeatureVertexMove": "FeatureVertexMove.gif",
    "Fang_von_Punkt": "Fang_von_Punkt.gif",
    "suchen": "suchen.gif",
    "V_Jpg-Tif": "V_Jpg-Tif.gif",
    "cut": "cut.gif",
    "cutmask": "cutmask.gif",
    "cutmaskdel": "cutmaskdel.gif",
    "Thumbs": "Thumbs.gif",
    "Einstellungen": "Einstellungen.gif",
    "butContactClip": "butContactClip.gif",
    "butOutsideClip": "butOutsideClip.gif",
    "butInsideClip": "butInsideClip.gif",
    "LineRe": "LineRe.gif",
    "go-next": "go-next.jpg",
    "NeuDS": "NeuDS.jpg",
    "Edit": "Edit.bmp",
    "media-floppy": "media-floppy.png",
    "floppyList": "floppyList.gif",
    "Filter": "Filter.gif",
    "FilterAllLayerEnt": "FilterAllLayerEnt.gif",
    "checked": "checked.gif",
    "unchecked": "unchecked.gif",
    "Ok": "Ok.png",
    "Ok_grau": "Ok_grau.png",
    "Sichtbar_an": "Sichtbar_an.gif",
    "Sichtbar_aus": "Sichtbar_aus.gif",
    "transp": "transp.png",
    "mActionSaveGCPpointsAs": "mActionSaveGCPpointsAs.png",
    "mActionLoadGCPpoints": "mActionLoadGCPpoints.png",
    "mActionAddGCPPoint": "mActionAddGCPPoint.png",
    "ordner-open": "ordner-open.png",
    "trash_icon": "trash_icon.png",
    "Befundnr": "Befundnr.gif",
    "Befundnr2": "Befundnr2.gif",
    "Profil": "Profil.gif",
    "Fund": "Fund.gif",
    "Probe": "Probe.gif",
    "einfügen": "einfügen.gif",
    "kopieren": "kopieren.gif",
}

icon_dir = dirname(__file__)
for icon_name, file_name in ICON_PATHS.items():
    ICON_PATHS[icon_name] = abspath(join(icon_dir, file_name))

list_of_paths = []
for icon_name, icon_path in ICON_PATHS.items():
    if not exists(icon_path):
        print("ICON_PATHS: file not found: " + icon_path, icon_name)
    if icon_path in list_of_paths:
        print("ICON_PATHS: duplicate entry found: " + icon_path, icon_name)
    list_of_paths.append(icon_path)

# for file_path in listdir(icon_dir):
#     if abspath(join(icon_dir, file_path)) not in list_of_paths:
#         print("ICON_PATHS: file not used? look also in .ui files: " + file_path)

del list_of_paths
del icon_dir
