

from PyQt5.QtWidgets import QDialog, QTableWidgetItem
from PyQt5.QtCore import QSettings

from lib.expertivity import calculateExpertivity

from ui_expertivitydialog import Ui_ExpertivityDialog

class ExpertivityDialog(QDialog):
  def __init__(self, rules, flux):
    QDialog.__init__(self)
    self.rules = rules
    self.flux = flux
    
    self.setModal(True)
    self.ui = Ui_ExpertivityDialog()
    self.ui.setupUi(self)
    
    R = len(rules)
    self.ui.tableWidget.setColumnCount(R)
    self.ui.tableWidget.setRowCount(R)
    
    ruleNames = [rule.name[:3] for rule in self.rules]
    self.ui.tableWidget.setHorizontalHeaderLabels(ruleNames)
    self.ui.tableWidget.setVerticalHeaderLabels(ruleNames)
    
    for i in range(R):
      self.ui.tableWidget.setColumnWidth(i, 50)
      
    s = QSettings()
    s.beginGroup('Expertivity')
    for i in range(R):
      s.beginGroup('Row%d' % i)
      for j in range(R):
        if j != i:
          self.ui.tableWidget.setItem(i, j, QTableWidgetItem(str(s.value('Column%d' % j, 0, float))))
      s.endGroup()
    s.endGroup()
    
    self.ui.tableWidget.itemChanged.connect(self.recalculateExpertivity)
    self.recalculateExpertivity();
    
  def getWeightAt(self, i, j):
    item = self.ui.tableWidget.item(i, j)
    if item:
      try:
        return float(item.text())
      except ValueError:
        pass
    
    return 0

  def getWeights(self):
    R = len(self.rules)
    weights = [[self.getWeightAt(i, j) for j in range(R)] for i in range(R)]
    return weights
    
  def recalculateExpertivity(self):
    w = self.getWeights()
    expertivity = calculateExpertivity(self.flux, w)
    self.ui.label.setText("Expertivity: %g" % expertivity)
    
  def saveOptions(self):
    R = len(self.rules)
    s = QSettings()
    s.beginGroup('Expertivity')
    for i in range(R):
      s.beginGroup('Row%d' % i)
      for j in range(R):
        if j != i:
          s.setValue('Column%d' % j, self.getWeightAt(i, j))
      s.endGroup()
    s.endGroup()
