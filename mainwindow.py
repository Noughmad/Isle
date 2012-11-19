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
from PyQt4.QtCore import *
from PyQt4.QtSvg import QSvgGenerator

from parser import *
from view import *
from ruleswidget import *
from optionswidget import *

import re
import chardet

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
  return COLORS[category % len(COLORS)]

class MainWindow(QMainWindow):
  def __init__(self):
    QMainWindow.__init__(self)


    self.parser = Parser()

    self.view = View(self)
    self.setCentralWidget(self.view)

    self.scene = QGraphicsScene(self)
    self.view.setScene(self.scene)
    self.margin = 5
    self.zoom = 1

    self.createActions()

    dock = QDockWidget(self)
    self.rw = RulesWidget(self)
    self.rw.rulesChanged.connect(self.displayIsle)
    dock.setWidget(self.rw)
    dock.setWindowTitle('ISLE Steps')
    self.addDockWidget(Qt.TopDockWidgetArea, dock)

    dock = QDockWidget(self)
    self.unmatchedWidget = QTreeWidget(self)
    self.unmatchedWidget.header().hide()
    self.unmatchedWidget.setRootIsDecorated(False)
    self.unmatchedWidget.setDragEnabled(True)
    self.unmatchedWidget.setDragDropMode(QAbstractItemView.DragOnly)
    dock.setWidget(self.unmatchedWidget)
    dock.setWindowTitle('Unmatched actions')
    self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    dock = QDockWidget(self)
    self.optionsWidget = OptionsWidget(self)
    self.optionsWidget.optionsChanged.connect(self.displayIsle)
    dock.setWidget(self.optionsWidget)
    dock.setWindowTitle('Options')
    self.addDockWidget(Qt.LeftDockWidgetArea, dock)

  def createActions(self):
    fileMenu = self.menuBar().addMenu("&File")
    load = QAction('Open', self)
    load.triggered.connect(self.loadFile)
    fileMenu.addAction(load)

    quit = QAction('Quit', self)
    quit.triggered.connect(qApp.quit)
    fileMenu.addAction(quit)

    imageMenu = self.menuBar().addMenu("&Image")
    save = QAction('Export image', self)
    save.triggered.connect(self.saveImage)
    imageMenu.addAction(save)

  def loadFile(self):
    name = QFileDialog.getOpenFileName(self, None, None, "HTML Files (*.html *.htm *.xhtml *.xml)")
    if name:
      self.loadFileByName(name)

  def loadFileByName(self, name):
    with open(name, 'rb') as f:
      content = f.read()
      encoding = chardet.detect(content)['encoding']
      self.parser.actions = []
      self.parser.feed(content.decode(encoding))
    self.calculatePH()
    self.displayIsle()
  
  def getCategories(self, action):
    cat = []
    i = 0
    for r in self.rw.rules():
      if any(r.match(s) for s in action.steps):
        cat.append(i)
      i = i + 1
    return cat

  def calculatePH(self):
    allHypotheses = {}
    for action in self.parser.actions:
      if len(action.phenomena) != 1:
        continue

      p = action.phenomena[0]
      if not p in allHypotheses:
        allHypotheses[p] = []
      for h in action.hypotheses:
        allHypotheses[p].append(h)

    self.hypoIndexes = {}
    self.hypoCounts = {}
    for p, hs in allHypotheses.items():
      hl = list(set(hs))
      hl.sort()
      i = 0
      for h in hl:
        self.hypoIndexes[h] = (p, i)
        i = i + 1
      self.hypoCounts[p] = len(hl)

  def displayIsle(self):
    self.scene.clear()
    if len(self.parser.actions) < 2:
      return

    offset = parseTime(self.parser.actions[0].start)
    endTime = parseTime(self.parser.actions[-1].end) - offset

    self.drawAxes(endTime, len(self.rw.rules()) * 100)

    self.unmatchedWidget.clear()
    colorOption = self.optionsWidget.colorOption()
    for action in self.parser.actions:
      x1 = parseTime(action.start) - offset
      x2 = parseTime(action.end) - offset
      categories = self.getCategories(action)
      if categories:
        for cat in categories:
          rule = self.rw.rules()[cat]
          if rule.name == 'Testing experiment' and action.judgment and self.optionsWidget.showJudgment():
            item = self.createActionItem(action, cat, QRectF(x1, cat*100+self.margin, x2-x1, 100-2*self.margin-15), colorOption)
            j = QGraphicsTextItem('J')
            j.setPos((x1+x2)/2 - 5, cat*100 + self.margin + 72)
            self.scene.addItem(j)
          else:
            item = self.createActionItem(action, cat, QRectF(x1, cat*100+self.margin, x2-x1, 100-2*self.margin), colorOption)
          item.setToolTip("%s - %s: %s" % (action.start, action.end, ', '.join(action.steps)))
          self.scene.addItem(item)
      else:
        item = QTreeWidgetItem(action.steps)
        self.unmatchedWidget.addTopLevelItem(item)

  def createActionItem(self, action, category, rect, colorOption):
    if colorOption == COLOR_PERSON:
      item = QGraphicsRectItem(rect)
      item.setBrush(self.getPersonColor(action.talkers))
    elif colorOption == COLOR_STEP:
      item = QGraphicsRectItem(rect)
      item.setBrush(categoryColor(category))
    else:
      n = len(action.hypotheses)
      item = QGraphicsRectItem(rect)
      if n:
        start = 0
        step = rect.height() / n
        item.setBrush(QBrush())
        item.setPen(QPen())
        for h in action.hypotheses:
          r = QRectF(rect.left(), rect.top() + start, rect.width(), step)
          i = QGraphicsRectItem(r, item)
          i.setBrush(self.getHypothesisColor(h))
          i.setPen(QPen(Qt.NoPen))
          start = start + step
      else:
        item.setBrush(Qt.darkGray)
    item.setPen(QPen(Qt.NoPen))
    return item

  def getPersonColor(self, talkers):
    if 'A' in talkers and 'B' in talkers:
      return Qt.darkMagenta
    elif 'A' in talkers:
      return Qt.red
    elif 'B' in talkers:
      return Qt.blue
    else:
      return Qt.gray

  def getHypothesisColor(self, hypothesis):
    (p, i) = self.hypoIndexes[hypothesis]
    n = self.hypoCounts[p]
    i = i/max(1, n-1)
    if p == 1:
      return QColor(255, 255*i, 0)
    else:
      return QColor(0, 255 - 255 * i + 100 * i * (1-i), 255*i + 100 * i * (1-i))

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

  def saveImage(self):
    name = QFileDialog.getSaveFileName(self, None, None, "Image Files (*.png *.jpg);;Vector Image Files (*.svg *.svgz)")
    if name:
      if name.endswith('.svg') or name.endswith('.svgz'):
        self.saveAsSvg(name)
      else:
        self.saveAsImage(name)

  def saveAsSvg(self, name):
    generator = QSvgGenerator()
    generator.setFileName(name)
    painter = QPainter()
    painter.begin(generator)
    self.scene.render(painter)
    painter.end()

  def saveAsImage(self, name):
    image = QImage(self.scene.sceneRect().size().toSize(), QImage.Format_RGB32)
    image.fill(Qt.white)
    painter = QPainter()
    painter.begin(image)
    self.scene.render(painter)
    painter.end()
    image.save(name)
