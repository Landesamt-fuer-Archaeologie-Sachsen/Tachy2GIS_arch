# -*- coding: utf-8 -*-

# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2022-04-12

from ..publisher import Publisher


class DataStorePlan:
    def __init__(self):

        print("init_dataStore_plan")

        self.pup = Publisher()

        self.profileNumber = None
        self.profil = None
        self.profilFoto = None
        self.view = None
        self.ebene = None
        self.gcps = None
        self.aarTransformationParamsHorizontal = None
        self.aarTransformationParamsAbsolute = None
        self.aarTransformationParamsOriginal = None
        self.epsg = None

    def addProfileNumber(self, profilnummer):
        self.profileNumber = profilnummer

    def getProfileNumber(self):
        return self.profileNumber

    def addProfile(self, profil):
        self.profil = profil

    def addEpsg(self, epsg):
        self.epsg = epsg

    def addProfileFoto(self, profilfoto):
        self.profilFoto = profilfoto

    def addView(self, blickrichtung):
        self.view = blickrichtung

    def addEntzerrungsebene(self, entzerrungsebene):
        self.ebene = entzerrungsebene

    def addGcps(self, gcps):
        self.gcps = gcps

    def addTransformParams(self, aarTransformationParams):

        if aarTransformationParams["aar_direction"] == "horizontal":
            self.aarTransformationParamsHorizontal = aarTransformationParams
        if aarTransformationParams["aar_direction"] == "absolute height":
            self.aarTransformationParamsAbsolute = aarTransformationParams
        if aarTransformationParams["aar_direction"] == "original":
            self.aarTransformationParamsOriginal = aarTransformationParams

    def getGcps(self):
        return self.gcps

    def getAarTransformationParams(self, aar_direction):

        if aar_direction == "horizontal":
            return self.aarTransformationParamsHorizontal
        if aar_direction == "absolute height":
            return self.aarTransformationParamsAbsolute
        if aar_direction == "original":
            return self.aarTransformationParamsOriginal

    def triggerAarTransformationParams(self, aar_direction):
        self.pup.publish("pushTransformationParams", self.getAarTransformationParams(aar_direction))
