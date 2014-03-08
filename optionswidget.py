"""
Copyright 2012 Miha Čančula <miha@noughmad.eu>
This file is part of Isle, a program for displaying transcripts.

This program is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with This program. If not, see http://www.gnu.org/licenses/.

"""

from PyQt4.QtGui import *
from PyQt4.QtCore import pyqtSignal, QSettings
from ui_optionswidget import Ui_OptionsWidget

from expertivitydialog import ExpertivityDialog

COLOR_PERSON = 1
COLOR_PERSON_GRAYSCALE = 5
COLOR_HYPOTHESIS = 2
COLOR_HYPOTHESIS_CONE = 4
COLOR_STEP = 3

TABS = [
  "Timeline",
  "Histogram",
  "Cycle"
]

class OptionsWidget(QWidget):

  optionsChanged = pyqtSignal()

  def __init__(self, parent):
    QWidget.__init__(self, parent)

    self.ui = Ui_OptionsWidget()
    self.ui.setupUi(self)

    for check in [self.ui.colorByPerson, self.ui.colorByHypothesis, self.ui.colorByStep, self.ui.showJudgment, self.ui.coloredStepsCheck, self.ui.transitionsRadioButton, self.ui.overlapRadioButton, self.ui.showGridLines, self.ui.colorOnlyCone, self.ui.colorGrayscale]:
      check.toggled.connect(self.optionsChanged)
    
    for slider in [self.ui.cycleRadiusSlider, self.ui.thicknessSlider, self.ui.stepSizeSlider, self.ui.arrowPositionSlider, self.ui.xScaleSlider, self.ui.yScaleSlider, self.ui.arrowPointSlider, self.ui.arrowSizeSlider, self.ui.numberOfParts]:
      slider.valueChanged.connect(self.optionsChanged)
      
    self.ui.splitMinutes.valueChanged.connect(self.optionsChanged)
    
    self.ui.tabWidget.currentChanged.connect(self.optionsChanged)
    
    self.optionsChanged.connect(self.saveOptions)
    self.loadOptions()

  def colorOption(self):
    if self.ui.colorByPerson.isChecked():
      return COLOR_PERSON_GRAYSCALE if self.ui.colorGrayscale.isChecked() else COLOR_PERSON
    elif self.ui.colorByHypothesis.isChecked():
      return COLOR_HYPOTHESIS_CONE if self.ui.colorOnlyCone.isChecked() else COLOR_HYPOTHESIS
    else:
      return COLOR_STEP
    
  def showJudgment(self):
    return self.ui.showJudgment.isChecked()
  
  def showGridLines(self):
    return self.ui.showGridLines.isChecked()
  
  def loadOptions(self):
    block = self.blockSignals(True)
    
    s = QSettings()
    s.beginGroup("Options")
    
    t = s.value("Tab", "Timeline", str)
    if t in TABS:
      self.ui.tabWidget.setCurrentIndex(TABS.index(t))
      
    s.beginGroup("Timeline")
    c = s.value("Color", "Hypothesis")
    if c == "Hypothesis":
      self.ui.colorByHypothesis.setChecked(True)
      self.ui.colorByPerson.setChecked(True)
    else:
      self.ui.colorByStep.setChecked(True)
      
    self.ui.colorOnlyCone.setChecked(s.value("ColorOnlyCone", True, bool))
    self.ui.colorOnlyCone.setEnabled(self.ui.colorByHypothesis.isChecked())

    self.ui.showJudgment.setChecked(s.value("JudgmentMarkers", True, bool))
    self.ui.showGridLines.setChecked(s.value("GridLines", True, bool))
    self.ui.xScaleSlider.setValue(s.value("ScaleX", 40, int))
    self.ui.yScaleSlider.setValue(s.value("ScaleY", 40, int))
    self.ui.splitMinutes.setValue(s.value("SplitMinutes", 35, int))
    s.endGroup()
    
    s.beginGroup("Cycle")
    self.ui.coloredStepsCheck.setChecked(s.value("Color", True, bool))
    if s.value("Connections") == "Overlap":
      self.ui.overlapRadioButton.setChecked(True)
    else:
      self.ui.transitionsRadioButton.setChecked(True)
    self.ui.cycleRadiusSlider.setValue(s.value("CycleRadius", 200, int))
    self.ui.stepSizeSlider.setValue(s.value("CircleSize", 15, int))
    self.ui.thicknessSlider.setValue(s.value("Thickness", 50, int))
    self.ui.arrowPositionSlider.setValue(s.value("ArrowPosition", 70, int))
    self.ui.arrowPointSlider.setValue(s.value("ArrowPoint", 5, int))
    self.ui.arrowSizeSlider.setValue(s.value("ArrowSize", 50, int))
    s.endGroup()
    
    s.beginGroup("Expertivity")
    self.ui.numberOfParts.setValue(s.value("NumberOfParts", 10, int))
    s.endGroup()
    
    self.blockSignals(block)
    self.optionsChanged.emit()
  
  def saveOptions(self):
    s = QSettings()
    s.beginGroup("Options")
    s.setValue("Tab", TABS[self.ui.tabWidget.currentIndex()])
    
    s.beginGroup("Timeline")
    if self.ui.colorByHypothesis.isChecked():
      s.setValue("Color", "Hypothesis")
    elif self.ui.colorByPerson.isChecked():
      s.setValue("Color", "Person")
    else:
      s.setValue("Color", "Step")
    s.setValue("ColorOnlyCone", self.ui.colorOnlyCone.isChecked())
    s.setValue("ScaleX", self.ui.xScaleSlider.value())
    s.setValue("ScaleY", self.ui.yScaleSlider.value())
    s.setValue("JudgmentMarkers", self.ui.showJudgment.isChecked())
    s.setValue("GridLines", self.ui.showGridLines.isChecked())
    s.setValue("SplitMinutes", self.ui.splitMinutes.value())
    s.endGroup()
    
    s.beginGroup("Cycle")
    s.setValue("Color", self.ui.coloredStepsCheck.isChecked())
    s.setValue("Connections", "Transitions" if self.ui.transitionsRadioButton.isChecked() else "Overlap")
    s.setValue("CycleRadius", self.ui.cycleRadiusSlider.value())
    s.setValue("CircleSize", self.ui.stepSizeSlider.value())
    s.setValue("Thickness", self.ui.thicknessSlider.value())
    s.setValue("ArrowPosition", self.ui.arrowPositionSlider.value())
    s.setValue("ArrowPoint", self.ui.arrowPointSlider.value())
    s.setValue("ArrowSize", self.ui.arrowSizeSlider.value())
    s.endGroup()
    
    s.beginGroup("Expertivity")
    s.setValue("NumberOfParts", self.ui.numberOfParts.value())
    s.endGroup()
    
    s.endGroup()
    s.sync()
