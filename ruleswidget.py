from PyQt4.QtGui import *
from PyQt4.QtCore import pyqtSignal
from ui_ruleswidget import Ui_RulesWidget

from rules import Rules

class RulesWidget(QWidget):

  rulesChanged = pyqtSignal()

  def __init__(self, parent):
    QWidget.__init__(self, parent)

    self.model = QStandardItemModel(self)
    self.ui = Ui_RulesWidget()
    self.ui.setupUi(self)

    self.ui.treeView.setModel(self.model)
    self.loadDefaultRules()

    self.ui.addCategoryButton.clicked.connect(self.addCategory)
    self.ui.addRuleButton.clicked.connect(self.addRule)
    self.ui.removeButton.clicked.connect(self.remove)

    self.model.dataChanged.connect(self.rulesChanged)

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
    self.rulesChanged.emit()

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
    self.rulesChanged.emit()