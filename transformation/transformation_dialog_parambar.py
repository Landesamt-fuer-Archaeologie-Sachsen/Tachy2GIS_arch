# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QSizePolicy


## @brief With the TransformationDialogParambar class a bar based on QWidget is realized
#
# Inherits from QWidget
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-11-09


class TransformationDialogParambar(QWidget):

    ## The constructor.
    # Creates labels with styles
    # @param dialogInstance pointer to the dialogInstance

    def __init__(self, dialogInstance):
        super(TransformationDialogParambar, self).__init__()

        self.dialogInstance = dialogInstance

        self.paramsBarLayout = QHBoxLayout()
        self.setLayout(self.paramsBarLayout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.paramLabel1 = QLabel()
        self.paramLabel1.setStyleSheet("color:  blue;")
        self.paramLabel2 = QLabel()
        self.paramLabel2.setStyleSheet("color:  blue;")
        self.paramLabel3 = QLabel()
        self.paramLabel3.setStyleSheet("color:  blue;")
        self.paramLabel4 = QLabel()
        self.paramLabel4.setStyleSheet("color:  blue;")
        self.paramLabel5 = QLabel()
        self.paramLabel5.setStyleSheet("color:  green;")
        self.paramLabel6 = QLabel()
        self.paramLabel6.setStyleSheet("color:  green;")

        self.setEmptyTransformationParamsBar()

        self.paramsBarLayout.addWidget(self.paramLabel1)
        self.paramsBarLayout.addWidget(self.createSplitter())
        self.paramsBarLayout.addWidget(self.paramLabel2)
        self.paramsBarLayout.addWidget(self.createSplitter())
        self.paramsBarLayout.addWidget(self.paramLabel3)
        self.paramsBarLayout.addWidget(self.createSplitter())
        self.paramsBarLayout.addWidget(self.paramLabel4)
        self.paramsBarLayout.addWidget(self.createSplitter())
        self.paramsBarLayout.addWidget(self.paramLabel5)
        self.paramsBarLayout.addWidget(self.createSplitter())
        self.paramsBarLayout.addWidget(self.paramLabel6)

    ## \brief Set text of the labels to none
    #
    def setEmptyTransformationParamsBar(self):
        self.paramLabel1.setText("Transl. X: none")
        self.paramLabel2.setText("Transl. Y: none")
        self.paramLabel3.setText("Rot.: none")
        self.paramLabel4.setText("SEM 2D: none")
        self.paramLabel5.setText("Transl. Z: none")
        self.paramLabel6.setText("SEM Z: none")

    ## \brief Update textvalue of the labels
    #
    # \param zAngle
    # \param translationX
    # \param translationY
    # \param globalError2D
    # \param translationZ
    # \param globalErrorZ

    def showTransformationParamsMessage(
        self, zAngle, translationX, translationY, globalError2D, translationZ, globalErrorZ
    ):
        self.paramLabel1.setText("Transl. X: " + str(round(translationX, 2)))
        self.paramLabel2.setText("Transl. Y: " + str(round(translationY, 2)))
        self.paramLabel3.setText("Rot.: " + str(round(zAngle, 2)))
        self.paramLabel4.setText("SEM 2D: " + str(round(globalError2D, 2)))
        self.paramLabel5.setText("Transl. Z: " + str(round(translationZ, 2)))
        self.paramLabel6.setText("SEM Z: " + str(round(globalErrorZ, 2)))

    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def createSplitter(self):
        vSplit = QFrame()
        vSplit.setFrameShape(QFrame.VLine | QFrame.Sunken)

        return vSplit
