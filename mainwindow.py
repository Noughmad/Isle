from PyQt4.QtGui import *
from PyQt4.QtCore import Qt, QPointF

from parser import Parser
from view import View
from ruleswidget import RulesWidget

import re

def parseTime(time):
  match = re.search('(\d+)[\.:](\d+)', time)
  if match:
    return 60 * int(match.group(1)) + int(match.group(2))
  else:
    return 0

def arrow():
  polygon = QPolygonF(4)
  polygon[0] = QPointF(0, 0)
  polygon[1] = QPointF(-8, -15)
  polygon[2] = QPointF(0, -10)
  polygon[3] = QPointF(8, -15)
  return polygon

COLORS = [
  Qt.red,
  Qt.green,
  Qt.blue,
  Qt.yellow,
  Qt.darkGray
]
def categoryColor(category):
  return COLORS[category]

class MainWindow(QMainWindow):
  def __init__(self):
    QMainWindow.__init__(self)


    self.parser = Parser()

    self.view = View(self)
    self.setCentralWidget(self.view)

    self.scene = QGraphicsScene(self)
    self.view.setScene(self.scene)
    self.margin = 2
    self.zoom = 1

    self.createActions()

    dock = QDockWidget(self)
    self.rw = RulesWidget(self)
    self.rw.rulesChanged.connect(self.displayIsle)
    dock.setWidget(self.rw)
    dock.setWindowTitle('ISLE Steps')

    dock = QDockWidget(self)
    self.unmatchedWidget = QTreeWidget(self)
    self.unmatchedWidget.header().hide()
    self.unmatchedWidget.setRootIsDecorated(False)
    self.unmatchedWidget.setDragEnabled(True)
    self.unmatchedWidget.setDragDropMode(QAbstractItemView.DragOnly)
    dock.setWidget(self.unmatchedWidget)
    dock.setWindowTitle('Unmatched actions')

  def createActions(self):
    fileMenu = self.menuBar().addMenu("&File")
    load = QAction('Open', self)
    load.triggered.connect(self.loadFile)
    fileMenu.addAction(load)

    quit = QAction('Quit', self)
    quit.triggered.connect(qApp.quit)
    fileMenu.addAction(quit)

  def loadFile(self):
    name = QFileDialog.getOpenFileName(self, None, None, "HTML Files (*.html *.htm *.xhtml *.xml)")
    if name:
      self.loadFileByName(name)

  def loadFileByName(self, name):
    with open(name, 'rt') as f:
      self.parser.feed(f.read())
    self.displayIsle()
  
  def getCategories(self, action):
    cat = []
    i = 0
    for r in self.rw.rules():
      if any(r.match(s) for s in action.steps):
        cat.append(i)
      i = i + 1
    return cat

  def displayIsle(self):
    self.scene.clear()
    if len(self.parser.actions) < 2:
      return

    offset = parseTime(self.parser.actions[0].start)
    endTime = parseTime(self.parser.actions[-1].end) - offset

    self.drawAxes(endTime, len(self.rw.rules()) * 100)

    self.unmatchedWidget.clear()
    for action in self.parser.actions:
      x1 = parseTime(action.start) - offset
      x2 = parseTime(action.end) - offset
      categories = self.getCategories(action)
      if categories:
        for cat in categories:
          item = QGraphicsRectItem(x1, cat*100+self.margin, x2-x1, 100-2*self.margin)
          item.setBrush(QBrush(categoryColor(cat)))
          item.setToolTip("%s - %s: %s" % (action.start, action.end, ', '.join(action.steps)))
          self.scene.addItem(item)
      else:
        item = QTreeWidgetItem(action.steps)
        self.unmatchedWidget.addTopLevelItem(item)

  def drawAxes(self, xMax, yMax):
    xAxis = QGraphicsLineItem(-10, yMax, xMax + 30, yMax)
    yAxis = QGraphicsLineItem(0, yMax + 10, 0, -30)

    xArrow = QGraphicsPolygonItem(arrow())
    xArrow.setPos(xMax + 30, yMax)
    xArrow.setRotation(-90)
    xArrow.setBrush(QBrush(Qt.black))

    for i in range(int(xMax/300+1)):
      tick = QGraphicsLineItem(i*300, yMax + 5, i*300, yMax + 1, xAxis)
      label = QGraphicsTextItem('%.2d:%.2d' % (i*5, 0), xAxis)
      label.setPos(i*300 - 22, yMax + 5)

    i = 0
    for rule in self.rw.rules():
      tick = QGraphicsLineItem(-5, i * 100, 6, i*100, yAxis)
      label = QGraphicsTextItem(rule.name, yAxis)
      label.setTextWidth(130)
      label.setPos(-150, 50 + i*100 - label.boundingRect().height()/2)
      i = i + 1

    yArrow = QGraphicsPolygonItem(arrow())
    yArrow.setPos(0, -30)
    yArrow.setRotation(180)
    yArrow.setBrush(QBrush(Qt.black))

    self.scene.addItem(xAxis)
    self.scene.addItem(yAxis)
    self.scene.addItem(xArrow)
    self.scene.addItem(yArrow)

    self.view.resetView()
