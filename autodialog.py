#
# <one line to give the program's name and a brief idea of what it does.>
# Copyright (C) 2013  Miha Cancula <email>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# 
#

from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtCore import QSettings

from ui_autodialog import Ui_AutoDialog

class AutoDialog(QDialog):
  def __init__(self):
    QDialog.__init__(self)
    self.setModal(True)
    self.ui = Ui_AutoDialog()
    self.ui.setupUi(self)
    
    s = QSettings()
    s.beginGroup('AutoDialog')
    self.ui.transcriptionFolderEdit.setText(s.value('TranscriptionFolder', '', str))
    self.ui.imageFolderEdit.setText(s.value('ImageFolder', '', str))
    self.ui.latexCheckBox.setChecked(s.value('GenerateLatex', True, bool))
    
    self.ui.transcriptionBrowseButton.clicked.connect(self.browseTranscriptions)
    self.ui.imageBrowseButton.clicked.connect(self.browseImages)
    
    self.ui.generateButton.clicked.connect(self.generateClicked)

  def transiption_folder(self):
    return self.ui.transcriptionFolderEdit.text()
  
  def image_folder(self):
    return self.ui.imageFolderEdit.text()
  
  def browseTranscriptions(self):
    self.ui.transcriptionFolderEdit.setText(QFileDialog.getExistingDirectory(self, "Choose directory with transcriptions", self.ui.transcriptionFolderEdit.text()))
    
  def browseImages(self):
    self.ui.imageFolderEdit.setText(QFileDialog.getExistingDirectory(self, "Choose directory for images", self.ui.imageFolderEdit.text()))
    
  def generateLatex(self):
    return self.ui.latexCheckBox.isChecked()

  def generateClicked(self):
    s = QSettings()
    s.beginGroup('AutoDialog')
    s.setValue('TranscriptionFolder', self.ui.transcriptionFolderEdit.text())
    s.setValue('ImageFolder', self.ui.imageFolderEdit.text())
    s.setValue('GenerateLatex', self.ui.latexCheckBox.isChecked())
    
    self.accept()