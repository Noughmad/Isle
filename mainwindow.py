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

from lib.parser import *
from view import *
from ruleswidget import *
from optionswidget import *
from autodialog import AutoDialog
from expertivitydialog import ExpertivityDialog
from lib import transitions

import subprocess

import re
import chardet
import math

def parseTime(time):
  match = re.search('(\d+)[\.:](\d+)', time)
  if match:
    return 60 * int(match.group(1)) + int(match.group(2))
  else:
    return 0

def arrow(y = 0):
  polygon = QPolygonF(4)
  polygon[0] = QPointF(0, y)
  polygon[1] = QPointF(-8, y-15)
  polygon[2] = QPointF(0, y-10)
  polygon[3] = QPointF(8, y-15)
  return polygon

COLORS = [
  QColor("orange"),
  QColor("limegreen"),
  QColor("gold"),
  QColor("royalblue"),
  QColor("red"),
  QColor("mediumturquoise"),
  QColor("orchid"),
  QColor("seagreen"),
  QColor("brown"),
  QColor("silver"),
  QColor("olive"),
  QColor("darkOrchid"),
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
    
    self.optionsWidget.ui.sourceStepComboBox.setModel(self.rw.model)

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
    
    generate = QAction("Generate all images", self)
    generate.triggered.connect(self.loadAndGenerateAll)
    imageMenu.addAction(generate)
    
    expertivity = QAction("Calculate Expertivity", self)
    expertivity.triggered.connect(self.showExpertivityDialog)
    imageMenu.addAction(expertivity)
    
  def loadFile(self):
    name = QFileDialog.getOpenFileName(self, None, None, "HTML Files (*.html *.htm *.xhtml *.xml)")
    if name:
      self.loadFileByName(name)

  def loadFileByName(self, name):
    with open(name, 'rb') as f:
      content = f.read()
      encoding = chardet.detect(content)['encoding']
      self.parser = Parser()
      self.parser.feed(content.decode(encoding))
    self.calculatePH()
    self.fixActionTimes()
    self._fluxMatrix = transitions.fluxMatrix(self.parser.actions, self.rw.rules())
    self._overlapMatrix = transitions.overlapMatrix(self.parser.actions, self.rw.rules())
    self.displayIsle()
  
  def getCategories(self, action):
    return transitions.getCategories(action, self.rw.rules())

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
      
  def fixActionTimes(self):
    offset = 0
    for i in range(len(self.parser.actions)):
      s = parseTime(self.parser.actions[i].startText)
      e = parseTime(self.parser.actions[i].endText)
      
      if i > 1 and s + offset < (self.parser.actions[i-1].start - 1800):
        offset = self.parser.actions[i-1].end
        
      self.parser.actions[i].start = s + offset
      self.parser.actions[i].end = e + offset

  def displayIsle(self):
    self.scene.clear()
    if len(self.parser.actions) < 2:
      return
    
    self.unmatchedWidget.clear()
    for action in self.parser.actions:
      if not self.getCategories(action):
        item = QTreeWidgetItem(action.steps)
        self.unmatchedWidget.addTopLevelItem(item)
    
    tab = self.optionsWidget.ui.tabWidget.currentIndex()
    if tab == 0:
      self.displayTimeline(self.optionsWidget.colorOption())
    elif tab == 1:
      self.displayHistogram()
    else:
      self.displayCycle()
      
    self.scene.setSceneRect(self.scene.itemsBoundingRect())
    
  def displayTimeline(self, colorOption):

    offset = self.parser.actions[0].start
    endTime = self.parser.actions[-1].end - offset
    
    X = self.optionsWidget.ui.xScaleSlider.value() / 30
    Y = self.optionsWidget.ui.yScaleSlider.value()
    self.margin = Y / 10

    R = len(self.rw.rules())
    self.drawAxes(endTime, R, X, Y)
    if self.optionsWidget.showGridLines():
      for i in range(R):
        line = QGraphicsLineItem(0, (i+0.5)*Y, endTime*X, (i+0.5)*Y)
        line.setPen(QPen(Qt.gray))
        self.scene.addItem(line)
      
    
    timeLabel = QGraphicsTextItem("Time [min]")
    timeLabel.setPos(X * endTime * 0.9, Y * (R+0.75))
    self.scene.addItem(timeLabel)

    for action in self.parser.actions:
      x1 = (action.start - offset) * X
      x2 = (action.end - offset) * X
      categories = self.getCategories(action)
      if categories:
        for cat in categories:
          rule = self.rw.rules()[cat]
          if rule.name == 'Testing experiment' and action.judgment and self.optionsWidget.showJudgment():
            item = self.createActionItem(action, cat, QRectF(x1, cat*Y+self.margin, x2-x1, Y-2*self.margin-15), colorOption)
            j = QGraphicsTextItem('J')
            j.setPos((x1+x2)/2 - 5, cat*Y + self.margin + 72*Y/100)
            self.scene.addItem(j)
          else:
            item = self.createActionItem(action, cat, QRectF(x1, cat*Y+self.margin, x2-x1, Y-2*self.margin), colorOption)
          item.setToolTip("%s - %s: %s" % (action.startText, action.endText, ', '.join(action.steps)))
          self.scene.addItem(item)

  def displayHistogram(self):
    R = self.rw.rules()
    cat_index = self.optionsWidget.ui.sourceStepComboBox.currentIndex()
    
    values = self._fluxMatrix[cat_index]
    for j in range(len(R)):
      print(R[j].name + " => " + str(values[j]))
      
    yMax = 50 * max(values)
    self.drawAxes(len(self.rw.rules()) * 100, yMax, 1, 100, histogramMax=max(values))
    for i in range(len(R)):
      item = QGraphicsRectItem(i * 100 + 10, yMax - values[i] * 50, 80, values[i] * 50)
      item.setBrush(Qt.blue)
      self.scene.addItem(item)
      
  def drawArrow(self, line, size, r1, r2):
    P = self.optionsWidget.ui.arrowPositionSlider.value() / 99
    position = line.pointAt(r1 / line.length()) * (1-P) + line.pointAt(1 - r2 / line.length()) * P
    item = QGraphicsPolygonItem(arrow(self.optionsWidget.ui.arrowPointSlider.value()))
    item.setScale(size / 3)
    item.setPos(position)
    item.setRotation(-90 - line.angle())
    item.setBrush(Qt.black)
    self.scene.addItem(item)
      
  def displayCycle(self):
    n = len(self.rw.rules())
    R = self.optionsWidget.ui.cycleRadiusSlider.value()
    T = self.optionsWidget.ui.thicknessSlider.value() / 66
    use_color = self.optionsWidget.ui.coloredStepsCheck.isChecked()
    
    times = self.getCategoryTimes()
    circles = [{
      'position' : (R * math.sin(2*math.pi*i/n), -R * math.cos(2*math.pi*i/n)), 
      'size' : math.sqrt(times[i] * self.optionsWidget.ui.stepSizeSlider.value() / 10), 
      'color' : categoryColor(i) if use_color else Qt.darkGray,
      'name' : self.rw.rules()[i].name
    } for i in range(n)]
    
    use_flux = self.optionsWidget.ui.transitionsRadioButton.isChecked()
    
    if use_flux:
      matrix = self._fluxMatrix
    else:
      matrix = self._overlapMatrix

    for source in range(n):
      for destination in range(source):
        v = (matrix[source][destination] + matrix[destination][source]) * 2 * T
        if not v:
          continue
        x1, y1 = circles[source]['position']
        x2, y2 = circles[destination]['position']
        line = QLineF(x1, y1, x2, y2)
        item = QGraphicsLineItem(line)
        pen = QPen()
        pen.setWidthF(0.5 * v)
        pen.setBrush(Qt.darkGray)
        item.setPen(pen)
        self.scene.addItem(item)
    
    for circle in circles:
      x, y = circle['position']
      size = circle['size']
      item = QGraphicsEllipseItem(x - size, y - size, 2*size, 2*size)
      item.setBrush(circle['color'])
      self.scene.addItem(item)
      
      text = QGraphicsTextItem(circle['name'])
      text.setPos(x, y)
      self.scene.addItem(text)
      
      if x > 1:
        text.setPos(x + size + 10, y - 10)
      elif x < -1:
        text.setPos(x - size - 10 - text.boundingRect().width(), y - 10)
      else:
        if y > 0:
          text.setPos(x - text.boundingRect().width()/2, y + size + 10)
        else:
          text.setPos(x - text.boundingRect().width()/2, y - size - 25)
          
    
    if use_flux:
      A = self.optionsWidget.ui.arrowSizeSlider.value() / 100
      for source in range(n):
        for destination in range(source):
          v = (matrix[source][destination] + matrix[destination][source]) * 2 * T
          if not v:
            continue
          x1, y1 = circles[source]['position']
          x2, y2 = circles[destination]['position']
          if matrix[source][destination]:
            self.drawArrow(QLineF(x1, y1, x2, y2), 0.5 + matrix[source][destination] * A, circles[source]['size'], circles[destination]['size'])
          if matrix[destination][source]:
            self.drawArrow(QLineF(x2, y2, x1, y1), 0.5 + matrix[destination][source] * A, circles[destination]['size'], circles[source]['size'])


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
    
  def getCategoryTimes(self):
    total = self.parser.actions[-1].end - self.parser.actions[0].start
    
    times = [0 for r in self.rw.rules()]
    for action in self.parser.actions:
      x1 = action.start
      x2 = action.end
      for cat in self.getCategories(action):
        times[cat] += (x2-x1)
    return [t*3600/total for t in times]

  def drawAxes(self, xMax, yMax, X, Y, histogramMax = 0):
    xAxis = QGraphicsLineItem(-10, yMax*Y, xMax*X + 30, yMax*Y)
    yAxis = QGraphicsLineItem(0, yMax*Y + 10, 0, -30)

    xArrow = QGraphicsPolygonItem(arrow())
    xArrow.setPos(xMax*X + 30, yMax*Y)
    xArrow.setRotation(-90)
    xArrow.setBrush(QBrush(Qt.black))

    if histogramMax:
      i = 0
      for rule in self.rw.rules():
        tick = QGraphicsLineItem(i*100, yMax - 5, i*100, yMax + 6, xAxis)
        label = QGraphicsTextItem(rule.name, xAxis)
        # label.setTextWidth(150)
        label.setPos(50 + i * 100, yMax + 4)
        label.setRotation(60)
        i = i + 1
      
      unitHeight = yMax / histogramMax
      for v in range(histogramMax+1):
        tick = QGraphicsLineItem(-5, yMax - v * unitHeight, 5, yMax - v * unitHeight)
        label = QGraphicsTextItem(str(v), yAxis)
        label.setPos(-20, yMax - v * unitHeight - label.boundingRect().height()/2)
      
    else:
      for i in range(int(xMax/300+1)):
        tick = QGraphicsLineItem(i*300*X, yMax*Y + 5, i*300*X, yMax*Y + 1, xAxis)
        label = QGraphicsTextItem('%.2d:%.2d' % (i*5, 0), xAxis)
        label.setPos(i*300*X - 22, yMax*Y + 5)

      i = 0
      for rule in self.rw.rules():
        tick = QGraphicsLineItem(-5, i * Y, 6, i*Y, yAxis)
        label = QGraphicsTextItem(rule.name, yAxis)
        label.setPos(-label.boundingRect().width() - 10, (0.5 + i) * Y - label.boundingRect().height()/2)
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
    generator.setSize(self.scene.sceneRect().size().toSize())
    painter = QPainter()
    painter.begin(generator)
    self.scene.render(painter)
    painter.end()

  def saveAsImage(self, name):
    image = QImage(self.scene.sceneRect().size().toSize(), QImage.Format_RGB32)
    image.fill(Qt.white)
    painter = QPainter()
    painter.begin(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)
    self.scene.render(painter)
    painter.end()
    image.save(name)
    
  def convertSvgToEps(self, image_name):
    subprocess.call(['inkscape', '-f', image_name + '.svg', '-A', image_name + '.pdf', '--export-latex'])
    
  def loadTranscriptionAndGenerateGraphs(self, transitions_file, image_file, latex):
    self.loadFileByName(transitions_file)
    
    colorings = {
      COLOR_STEP : 'step',
      COLOR_PERSON : 'person',
      COLOR_HYPOTHESIS : 'hypothesis',
    }
    
    for color_option, name in colorings.items():
      self.scene.clear()
      self.displayTimeline(color_option)
      self.scene.setSceneRect(self.scene.itemsBoundingRect())
      self.saveAsSvg(image_file + '_timeline_' + name + '.svg')
      if latex:
        self.convertSvgToEps(image_file + '_timeline_' + name)
    
    self.scene.clear()
    self.displayCycle()
    self.scene.setSceneRect(self.scene.itemsBoundingRect())
    self.saveAsSvg(image_file + '_cycle.svg')
    if latex:
      self.convertSvgToEps(image_file + '_cycle')
    
  def loadAndGenerateAll(self):
    dialog = AutoDialog()
    if (dialog.exec_() == QDialog.Accepted):
      trans_dir = QDir(dialog.transiption_folder())
      image_dir = dialog.image_folder()
      latex = dialog.generateLatex()
      
      for info in trans_dir.entryInfoList(["*.html"]):
        qDebug(info.absoluteFilePath())
        trans_file = info.absoluteFilePath()
        base = info.baseName().replace('transcription_', '')
        image_out = image_dir + '/' + base
        self.loadTranscriptionAndGenerateGraphs(trans_file, image_out, latex)
      
  def showExpertivityDialog(self):
    dialog = ExpertivityDialog(self.rw.rules(), self._fluxMatrix)
    dialog.exec_()
