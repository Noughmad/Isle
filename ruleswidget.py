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
from ui_ruleswidget import Ui_RulesWidget

from lib.rules import Rules

class RulesWidget(QWidget):

  rulesChanged = pyqtSignal()

  def __init__(self, parent):
    QWidget.__init__(self, parent)

    self.model = QStandardItemModel(self)
    self.ui = Ui_RulesWidget()
    self.ui.setupUi(self)

    self.ui.treeView.setModel(self.model)
    self.loadRules()
    if (self.model.invisibleRootItem().rowCount() == 0):
      self.loadDefaultRules()

    self.ui.addCategoryButton.clicked.connect(self.addCategory)
    self.ui.addRuleButton.clicked.connect(self.addRule)
    self.ui.removeButton.clicked.connect(self.remove)

    self.model.dataChanged.connect(self.saveAndNotify)

  def saveAndNotify(self):
    s = QSettings(self)
    rules = self.rules()
    s.setValue('RuleNames', [r.name for r in rules])
    s.beginGroup('Rules')
    for r in rules:
      s.beginGroup(r.name)
      s.setValue('Name', r.name)
      s.setValue('Rules', r.rules)
      s.endGroup()
    s.endGroup()
    s.sync()
    self.rulesChanged.emit()

  def rules(self):
    ret = []
    for i in range(self.model.invisibleRootItem().rowCount()):
      categoryItem = self.model.invisibleRootItem().child(i)
      r = Rules()
      r.name = categoryItem.text()
      for j in range(categoryItem.rowCount()):
        ruleItem = categoryItem.child(j)
        r.rules.append(ruleItem.text())
      ret.append(r)
    return ret

  def loadRules(self):
    s = QSettings(self)
    names = s.value('RuleNames')
    s.beginGroup('Rules')
    if not names:
      return
    for n in names:
      s.beginGroup(n)
      item = QStandardItem(s.value('Name'))
      rules = s.value('Rules')
      if rules:
        for rule in rules:
          item.appendRow(QStandardItem(rule))
      self.model.invisibleRootItem().appendRow(item)
      s.endGroup()

    s.endGroup()
    self.saveAndNotify()

  def loadDefaultRules(self):
    obs = QStandardItem('Observation')
    obs.appendRow(QStandardItem('Observation'))
    self.model.invisibleRootItem().appendRow(obs)

    obs = QStandardItem('Formulation of hypothesis')
    obs.appendRow(QStandardItem('hypothesis'))
    self.model.invisibleRootItem().appendRow(obs)

    obs = QStandardItem('Testing experiment')
    obs.appendRow(QStandardItem('experiment'))
    self.model.invisibleRootItem().appendRow(obs)

    obs = QStandardItem('Prediction')
    obs.appendRow(QStandardItem('Prediction'))
    self.model.invisibleRootItem().appendRow(obs)

  def addCategory(self):
    cat = QStandardItem('New Category')
    cat.appendRow(QStandardItem('New Rule'))
    self.model.invisibleRootItem().appendRow(cat)
    self.ui.treeView.expand(cat.index())
    self.saveAndNotify()

  def addRule(self):
    idx = self.ui.treeView.selectedIndexes()
    if not idx or idx[0].parent().isValid():
      return
    parent = self.model.itemFromIndex(idx[0])
    rule = QStandardItem('New Rule')
    parent.appendRow(rule)
    self.rulesChanged.emit()

  def remove(self):
    idx = self.ui.treeView.selectedIndexes()
    if not idx:
      return
    self.model.removeRows(idx[0].row(), 1, idx[0].parent())
    self.saveAndNotify()
