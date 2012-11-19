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
from PyQt4.QtCore import pyqtSignal
from ui_optionswidget import Ui_OptionsWidget

COLOR_PERSON = 1
COLOR_HYPOTHESIS = 2
COLOR_STEP = 3

class OptionsWidget(QWidget):

  optionsChanged = pyqtSignal()

  def __init__(self, parent):
    QWidget.__init__(self, parent)

    self.ui = Ui_OptionsWidget()
    self.ui.setupUi(self)

    for check in [self.ui.colorByPerson, self.ui.colorByHypothesis, self.ui.colorByStep, self.ui.showJudgment]:
      check.toggled.connect(self.optionsChanged)

  def colorOption(self):
    if self.ui.colorByPerson.isChecked():
      return COLOR_PERSON
    elif self.ui.colorByHypothesis.isChecked():
      return COLOR_HYPOTHESIS
    else:
      return COLOR_STEP
    
  def showJudgment(self):
    return self.ui.showJudgment.isChecked()