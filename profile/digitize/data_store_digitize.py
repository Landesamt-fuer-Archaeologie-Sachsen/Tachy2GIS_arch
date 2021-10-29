# -*- coding: utf-8 -*-

## @brief With the TransformationDialogParambar class a bar based on QWidget is realized
#
# Inherits from QWidget
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-11-09

from ..publisher import Publisher

class DataStoreDigitize():

    ## The constructor.
    # Creates labels with styles
    # @param dialogInstance pointer to the dialogInstance

    def __init__(self):

        print('init_dataStore_digitize')

        self.pup = Publisher()

        self.profileNumber = None
        self.profil = None
        self.profilFoto = None
        self.view = None
        self.ebene = None
        self.gcps = None
        self.aarTransformationParams = None
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
        self.aarTransformationParams = aarTransformationParams

    def getGcps(self):
        return self.gcps

    def getAarTransformationParams(self):

        return self.aarTransformationParams

    def triggerAarTransformationParams(self):

        print('hhhhhhhhhhhhhhuuuuu', self.getAarTransformationParams())
        self.pup.publish('pushTransformationParams', self.getAarTransformationParams())
