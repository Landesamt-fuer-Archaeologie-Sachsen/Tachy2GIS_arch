# -*- coding: utf-8 -*-

## @brief With the TransformationDialogParambar class a bar based on QWidget is realized
#
# Inherits from QWidget
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-11-09

from ..publisher import Publisher


class DataStoreGeoref:

    ## The constructor.
    # Creates labels with styles
    # @param dialogInstance pointer to the dialogInstance

    def __init__(self):

        self.pup = Publisher()
        self.imagePoints = []
        self.targetPoints = []
        self.aarPointsHorizontal = []
        self.aarPointsOriginal = []
        self.aarPointsAbsolute = []
        self.aarTransformationParamsHorizontal = {}
        self.aarTransformationParamsAbsolute = {}
        self.aarTransformationParamsOriginal = {}

    ## \brief Add image point
    #
    # @param pointObj is a dictionary e.G.:
    #  \code{.py}
    # {
    #   'obj_uuid': '{ff4533b8-2e88-4f52-ac24-bb98c345c90b}',
    #   'x': 231.0,
    #   'z': -228.0
    # }
    #  \endcode
    #
    def addImagePoint(self, pointObj):

        if len(self.imagePoints) == 0:

            self.imagePoints.append({"obj_uuid": pointObj["obj_uuid"], "x": pointObj["x"], "z": pointObj["z"]})
        else:
            checker = False
            for statePoint in self.imagePoints:

                if statePoint["obj_uuid"] == pointObj["obj_uuid"]:
                    statePoint["x"] = pointObj["x"]
                    statePoint["z"] = pointObj["z"]
                    checker = True

            if checker == False:
                self.imagePoints.append({"obj_uuid": pointObj["obj_uuid"], "x": pointObj["x"], "z": pointObj["z"]})

    def addTargetPoints(self, refData):

        self.targetPoints = []

        for pointObj in refData["targetGCP"]["points"]:
            self.targetPoints.append(
                {"obj_uuid": pointObj["obj_uuid"], "x": pointObj["x"], "y": pointObj["z"], "z": pointObj["z"]}
            )

    def addAarPoints(self, aarList):

        aarDirection = aarList["aar_direction"]

        if aarDirection == "original":

            aarArray = []
            # Punkte
            for pointObj in aarList["coord_trans"]:
                aarArray.append(
                    {
                        "obj_uuid": pointObj[8],
                        "ptnr": str(pointObj[7]),
                        "x": pointObj[0],
                        "y": pointObj[1],
                        "z": pointObj[2],
                        "z_org": pointObj[4],
                        "distance": pointObj[5],
                        "usage": pointObj[6],
                    }
                )

            self.pup.publish("pushAarPoints", aarArray)

            self.aarPointsOriginal = aarArray

            # Transformationsparameter
            transformationParams = aarList["transformationParams"]
            z_slope = aarList["linegress"][0]
            z_intercept = aarList["linegress"][1]
            transformationParams["z_slope"] = z_slope
            transformationParams["z_intercept"] = z_intercept
            transformationParams["ns_error"] = aarList["ns_error"]

            self.updateAarTransformationParams(transformationParams)

        if aarDirection == "absolute height":

            aarArray = []
            # Punkte
            for pointObj in aarList["coord_trans"]:
                aarArray.append(
                    {
                        "obj_uuid": pointObj[8],
                        "ptnr": str(pointObj[7]),
                        "x": pointObj[0],
                        "y": pointObj[1],
                        "z": pointObj[2],
                        "z_org": pointObj[4],
                        "distance": pointObj[5],
                        "usage": pointObj[6],
                    }
                )

            self.pup.publish("pushAarPoints", aarArray)

            self.aarPointsAbsolute = aarArray

            # Transformationsparameter
            transformationParams = aarList["transformationParams"]
            z_slope = aarList["linegress"][0]
            z_intercept = aarList["linegress"][1]
            transformationParams["z_slope"] = z_slope
            transformationParams["z_intercept"] = z_intercept
            transformationParams["ns_error"] = aarList["ns_error"]

            self.updateAarTransformationParams(transformationParams)

        if aarDirection == "horizontal":

            aarArray = []
            # Punkte
            for pointObj in aarList["coord_trans"]:
                aarArray.append(
                    {
                        "obj_uuid": pointObj[8],
                        "ptnr": str(pointObj[7]),
                        "x": pointObj[0],
                        "y": pointObj[1],
                        "z": pointObj[2],
                        "z_org": pointObj[4],
                        "distance": pointObj[5],
                        "usage": pointObj[6],
                    }
                )

            self.pup.publish("pushAarPoints", aarArray)

            self.aarPointsHorizontal = aarArray

            # Transformationsparameter
            transformationParams = aarList["transformationParams"]
            z_slope = aarList["linegress"][0]
            z_intercept = aarList["linegress"][1]
            transformationParams["z_slope"] = z_slope
            transformationParams["z_intercept"] = z_intercept
            transformationParams["ns_error"] = aarList["ns_error"]

            self.updateAarTransformationParams(transformationParams)

    def updateAarTransformationParams(self, params):
        if params["aar_direction"] == "horizontal":
            self.aarTransformationParamsHorizontal = params
        if params["aar_direction"] == "absolute height":
            self.aarTransformationParamsAbsolute = params
        if params["aar_direction"] == "original":
            self.aarTransformationParamsOriginal = params

        self.pup.publish("pushTransformationParams", self.getAarTransformationParams(params["aar_direction"]))

    def getAarTransformationParams(self, aar_direction):

        if aar_direction == "horizontal":
            return self.aarTransformationParamsHorizontal
        if aar_direction == "absolute height":
            return self.aarTransformationParamsAbsolute
        if aar_direction == "original":
            return self.aarTransformationParamsOriginal

    def getGeorefData(self, aarDirection):

        if aarDirection == "horizontal":
            retPoints = self.aarPointsHorizontal

        if aarDirection == "original":
            retPoints = self.aarPointsOriginal

        if aarDirection == "absolute height":
            retPoints = self.aarPointsAbsolute

        georefData = []

        for aarObj in retPoints:
            if aarObj["usage"] == 1:
                for imageObj in self.imagePoints:
                    if aarObj["obj_uuid"] == imageObj["obj_uuid"]:
                        georefData.append(
                            {
                                "obj_uuid": aarObj["obj_uuid"],
                                "ptnr": aarObj["ptnr"],
                                "input_x": imageObj["x"],
                                "input_z": imageObj["z"],
                                "aar_x": aarObj["x"],
                                "aar_y": aarObj["y"],
                                "aar_z": aarObj["z"],
                                "aar_z_org": aarObj["z_org"],
                                "aar_distance": aarObj["distance"],
                                "aar_direction": aarDirection,
                            }
                        )
        return georefData

    def clearStore(self):

        self.imagePoints = []
        self.targetPoints = []
        self.aarPointsHorizontal = []
        self.aarPointsOriginal = []
        self.aarPointsAbsolute = []
        self.aarTransformationParamsHorizontal = {}
        self.aarTransformationParamsAbsolute = {}
        self.aarTransformationParamsOriginal = {}
