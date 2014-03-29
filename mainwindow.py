# -*- coding: utf-8 -*-

"""
Copyright 2012 Miha ÄanÄula <miha@noughmad.eu>
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

from lib import transitions, expertivity

import subprocess

import re
import math


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
    self.optionsWidget.ui.weightsButton.clicked.connect(self.showExpertivityDialog)
    dock.setWidget(self.optionsWidget)
    dock.setWindowTitle('Options')
    self.addDockWidget(Qt.LeftDockWidgetArea, dock)
    
    self.timelineFont = QFont()
    self.timelineFont.setFamily("Times")
    self.timelineFont.setPointSize(9)
    
    self.transitionFont = QFont()
    self.transitionFont.setFamily("Times")
    self.transitionFont.setPointSize(12)
    
  def alignRight(self, item):
    fmt = QTextBlockFormat()
    fmt.setAlignment(Qt.AlignRight)
    cursor = item.textCursor()
    cursor.select(QTextCursor.Document)
    cursor.mergeBlockFormat(fmt)
    cursor.clearSelection()
    item.setTextCursor(cursor)
    
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
      try:
        import chardet
        encoding = chardet.detect(content)['encoding']
      except ImportError:
        encoding = "utf-8"

      self.parser = Parser()
      try:
        self.parser.feed(content.decode(encoding))
      except UnicodeDecodeError:
        print ("You are trying to load a file with invalid Unicode characters, probably generated by MS Word")
        print ("Either use valid Unicode, such as that generated by LibreOffice, or install module \"chardet\"")
        return

    self.calculatePH()
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
        if not h in allHypotheses[p]:
          allHypotheses[p].append(h)

    self.hypoIndexes = {}
    self.hypoCounts = {}
    for p, hs in allHypotheses.items():
      i = 0
      for h in hs:
        self.hypoIndexes[h] = (p, i)
        i = i + 1
      self.hypoCounts[p] = len(hs)
      

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
      
      if self.optionsWidget.ui.transitionsRadioButton.isChecked():
        self.displayCycle(self._fluxMatrix, True)
      else:
        self.displayCycle(self._overlapMatrix, False)
    else:
      self.displayExpertivity()
      
    self.scene.setSceneRect(self.scene.itemsBoundingRect())
    
  def displayLegend(self, colorOption):
    
    Y = 100
    self.margin = 10
    
    if colorOption == COLOR_PERSON_GRAYSCALE:
      m = self.margin
      q = int((Y - 2 * m)/2)
      s = 2*q

      self.patternImage = QImage(QSize(s,s), QImage.Format_ARGB32)
      
      p = QPainter()
      p.begin(self.patternImage)
      p.fillRect(0, 0, q, m, Qt.darkGray)
      p.fillRect(0, m, q, q, Qt.lightGray)
      p.fillRect(0, m + q, q, q-m, Qt.darkGray)

      p.fillRect(q, 0, q, m, Qt.lightGray)
      p.fillRect(q, m, q, q, Qt.darkGray)
      p.fillRect(q, m + q, q, q-m, Qt.lightGray)
      p.end()      
    w = Y - 2*self.margin
    
    A = Action()
    A.talkers.add('A')
    
    B = Action()
    B.talkers.add('B')
    
    AB = Action()
    AB.talkers.add('A')
    AB.talkers.add('B')
    
    spacing = 350
    
    rectA = self.createActionItem(A, None, QRectF(0, self.margin, w, w), colorOption, None)
    rectB = self.createActionItem(B, None, QRectF(spacing, self.margin, w, w), colorOption, None)
    rectAB = self.createActionItem(AB, None, QRectF(2*spacing, self.margin, w, w), colorOption, None)
    
    self.scene.addItem(rectA)
    self.scene.addItem(rectB)
    self.scene.addItem(rectAB)
    
    font = self.timelineFont
    font.setPointSize(32)
    
    textA = QGraphicsTextItem("Person A")
    textA.setPos(Y, self.margin + 12)
    textA.setFont(font)
    
    textB = QGraphicsTextItem("Person B")
    textB.setPos(Y + spacing, self.margin + 12)
    textB.setFont(font)
    
    textAB = QGraphicsTextItem("Both")
    textAB.setPos(Y + 2*spacing, self.margin + 12)
    textAB.setFont(font)
    
    self.scene.addItem(textA)
    self.scene.addItem(textB)
    self.scene.addItem(textAB)

    
  def displayTimeline(self, colorOption):

    offset = self.parser.actions[0].start
    endTime = self.parser.actions[-1].end - offset
    
    X = self.optionsWidget.ui.xScaleSlider.value() / 30
    Y = 10 * int(self.optionsWidget.ui.yScaleSlider.value() / 10)
    self.margin = Y / 10
        
    SplitTime = self.optionsWidget.ui.splitMinutes.value() * 60
    NumParts = math.ceil(float(endTime) / SplitTime)
    R = len(self.rw.rules())
    GraphHeight = (R + 2.5) * Y
    
    if NumParts == 1:
      SplitTime = endTime
      
    if colorOption == COLOR_PERSON_GRAYSCALE:
      m = self.margin
      q = int((Y - 2 * m)/4)
      s = 2*q

      self.patternImage = QImage(QSize(s,s), QImage.Format_ARGB32)
      
      p = QPainter()
      p.begin(self.patternImage)
      p.fillRect(0, 0, q, m, Qt.darkGray)
      p.fillRect(0, m, q, q, Qt.lightGray)
      p.fillRect(0, m + q, q, q, Qt.darkGray)

      p.fillRect(q, 0, q, m, Qt.lightGray)
      p.fillRect(q, m, q, q, Qt.darkGray)
      p.fillRect(q, m + q, q, q, Qt.lightGray)
      p.end()
    
    for i in range(NumParts):
      base = QGraphicsRectItem(0, 0, 0, 0)
      base.setPos(0, i * GraphHeight)
      self.drawAxes(SplitTime, R, X, Y, base, xStartMinutes=i*SplitTime / 60)
      if self.optionsWidget.showGridLines():
        for ir in range(R):
          line = QGraphicsLineItem(0, (ir+0.5)*Y, SplitTime*X, (ir+0.5)*Y, base)
          line.setPen(QPen(Qt.gray))
    
      timeLabel = QGraphicsTextItem("Time [min]", base)
      timeLabel.setFont(self.timelineFont)
      timeLabel.setPos(X * SplitTime * 0.9, Y * (R+0.75))
      
      for action in [a for a in self.parser.actions if (a.end - offset) >= i * SplitTime and (a.start - offset) <= (i+1) * SplitTime]:
        x1 = max([action.start - offset - i * SplitTime, 0]) * X
        x2 = min([action.end - offset - i * SplitTime, SplitTime]) * X
        categories = self.getCategories(action)
        if categories:
          for cat in categories:
            rule = self.rw.rules()[cat]
            if rule.name == 'Testing experiment' and action.judgment and self.optionsWidget.showJudgment():
              item = self.createActionItem(action, cat, QRectF(x1, cat*Y+self.margin, x2-x1, Y-2*self.margin-15), colorOption, base)
              j = QGraphicsTextItem('J', base)
              j.setFont(self.timelineFont)
              j.setPos((x1+x2)/2 - 5, cat*Y + self.margin + 72*Y/100)
            else:
              item = self.createActionItem(action, cat, QRectF(x1, cat*Y+self.margin, x2-x1, Y-2*self.margin), colorOption, base)
            item.setToolTip("%s - %s: %s" % (action.startText, action.endText, ', '.join(action.steps)))
      self.scene.addItem(base)

  def displayExpertivity(self):
    parts = self.optionsWidget.ui.numberOfParts.value()
    T = self.parser.duration() / parts
    Height = 10.0
    
    R = len(self.rw.rules())
    weights = expertivity.loadWeights(R)
    points = []
    for actions in self.parser.get_actions(parts):
      flux = transitions.fluxMatrix(actions, self.rw.rules())
      e = expertivity.calculateExpertivity(flux, weights)
      points.append(e)
      
    yMax = max(points)
    yMin = min(points)
    
    if yMax == yMin:
      return
    
    lMax = int(math.floor(math.log10(abs(yMax))))
    lMin = int(math.floor(math.log10(abs(yMin))))
    l = max([lMax, lMin])
    
    rMax = round(yMax, -l)
    rMin = round(yMin, -l)

    if (rMin > yMin):
      rMin -= math.pow(10, l)

    if (rMax < yMax):
      rMax += math.pow(10, l)

    yMax = rMax
    yMin = rMin

    step = math.pow(10, l)
    if step >= (yMax - yMin):
      step /= 10
    elif step >= (yMax - yMin) / 2:
      step /= 5
    elif step >= (yMax - yMin) / 5:
      step /= 2
      
    
    yScale = Height / (yMax - yMin)

    X = self.optionsWidget.ui.xScaleSlider.value() / 30
    Y = self.optionsWidget.ui.yScaleSlider.value()

    self.drawAxes(parts * T, Height, X, Y, parentItem=None, labels=False)
    timeLabel = QGraphicsTextItem("Time [min]")
    timeLabel.setFont(self.timelineFont)
    timeLabel.setPos(X * T * parts * 0.9, Y * (Height+0.75))
    self.scene.addItem(timeLabel)
      
    for i in range(parts):
      point = QGraphicsEllipseItem(T*(i+0.5)*X - 3, Height * Y - (points[i]-yMin)*Y*yScale - 3, 6, 6)
      point.setBrush(QBrush(Qt.red))
      point.setPen(QPen(Qt.NoPen))
      if (i != 0):  
        line = QGraphicsLineItem(T*(i-0.5)*X, Height * Y - (points[i-1]-yMin)*Y*yScale, T*(i+0.5)*X, Height * Y - (points[i]-yMin)*Y*yScale)
        pen = QPen()
        pen.setColor(Qt.red)
        pen.setWidth(3)
        line.setPen(pen)
        self.scene.addItem(line)
      
      tick = QGraphicsLineItem((i+1)*T*X, Height*Y + 5, (i+1)*T*X, Height*Y + 1)
      t = T*(i+1)
      minutes = int(t / 60)
      secs = int(t) % 60
      label = QGraphicsTextItem('%.2d:%.2d' % (minutes, secs))
      label.setFont(self.timelineFont)
      label.setPos((i+1)*T*X - 22, Height*Y + 5)
      
      self.scene.addItem(point)
      self.scene.addItem(tick)
      self.scene.addItem(label)
      
    label = QGraphicsTextItem('00:00')
    label.setPos(-22, Height*Y + 5)
    self.scene.addItem(label)
    
    y = 0.0
    while y <= (yMax-yMin):
      tick = QGraphicsLineItem(-5, (Height - y * yScale) * Y, 6, (Height - y * yScale) * Y)
      label = QGraphicsTextItem("%g" % (y + yMin))
      label.setPos(-label.boundingRect().width() - 10, (Height - y * yScale) * Y - label.boundingRect().height()/2)
      self.scene.addItem(tick)
      self.scene.addItem(label)
      y += step

  def drawArrow(self, line, size, r1, r2):
    P = self.optionsWidget.ui.arrowPositionSlider.value() / 99
    position = line.pointAt(r1 / line.length()) * (1-P) + line.pointAt(1 - r2 / line.length()) * P
    item = QGraphicsPolygonItem(arrow(self.optionsWidget.ui.arrowPointSlider.value()))
    item.setScale(size / 3)
    item.setPos(position)
    item.setRotation(-90 - line.angle())
    item.setBrush(Qt.black)
    self.scene.addItem(item)
      
  def displayCycle(self, matrix, use_flux):
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
      text.setFont(self.transitionFont)
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


  def createActionItem(self, action, category, rect, colorOption, base):
    if colorOption in [COLOR_PERSON, COLOR_PERSON_GRAYSCALE]:
      item = QGraphicsRectItem(rect, base)
      item.setBrush(self.getPersonColor(action.talkers, colorOption))
    elif colorOption == COLOR_STEP:
      item = QGraphicsRectItem(rect, base)
      item.setBrush(categoryColor(category))
    else:
      n = len(action.hypotheses)
      item = QGraphicsRectItem(rect, base)
      if n:
        start = 0
        step = rect.height() / n
        item.setBrush(QBrush())
        item.setPen(QPen())
        for h in action.hypotheses:
          r = QRectF(rect.left(), rect.top() + start, rect.width(), step)
          i = QGraphicsRectItem(r, item)
          if colorOption == COLOR_HYPOTHESIS or 0 in action.phenomena:
            i.setBrush(self.getHypothesisColor(h))
          else:
            i.setBrush(Qt.darkGray)
          i.setPen(QPen(Qt.NoPen))
          start = start + step
      else:
        item.setBrush(Qt.darkGray)
    item.setPen(QPen(Qt.NoPen))
    return item

  def getPersonColor(self, talkers, colorOption):
    if colorOption == COLOR_PERSON_GRAYSCALE:
      if 'A' in talkers and 'B' in talkers:
        b = QBrush()
        b.setTextureImage(self.patternImage)
        return b
      elif 'A' in talkers:
        return Qt.lightGray
      elif 'B' in talkers:
        return Qt.darkGray
      else:
        return Qt.gray
    else:
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
    
    if (i % 2) == 0:
      f = float(i)/max([1, n]) * 0.5
    else:
      f = 0.5 + float(i)/max([1, n]) * 0.5

    if p == 0:
      return QColor.fromHsv(360 * f, 255, 255)
    else:
      return QColor(0, 255 - 255 * f + 100 * f * (1-f), 255*f + 100 * f * (1-f))
    
  def getCategoryTimes(self):
    total = self.parser.actions[-1].end - self.parser.actions[0].start
    
    times = [0 for r in self.rw.rules()]
    for action in self.parser.actions:
      x1 = action.start
      x2 = action.end
      for cat in self.getCategories(action):
        times[cat] += (x2-x1)
    return [t*3600/total for t in times]

  def drawAxes(self, xMax, yMax, X, Y, parentItem = None, labels = True, xStartMinutes = 0):
    xAxis = QGraphicsLineItem(-10, yMax*Y, xMax*X + 30, yMax*Y, parentItem)
    yAxis = QGraphicsLineItem(0, yMax*Y + 10, 0, -30, parentItem)

    xArrow = QGraphicsPolygonItem(arrow(), parentItem)
    xArrow.setPos(xMax*X + 30, yMax*Y)
    xArrow.setRotation(-90)
    xArrow.setBrush(QBrush(Qt.black))

    if labels:
      for i in range(int(xMax/300+1)):
        tick = QGraphicsLineItem(i*300*X, yMax*Y + 5, i*300*X, yMax*Y + 1, xAxis)
        label = QGraphicsTextItem('%.2d:%.2d' % (i*5 + xStartMinutes, 0), xAxis)
        label.setFont(self.timelineFont)
        label.setPos(i*300*X - label.boundingRect().width()/2, yMax*Y + 5)

      i = 0
      for rule in self.rw.rules():
        tick = QGraphicsLineItem(-5, i * Y, 6, i*Y, yAxis)
        label = QGraphicsTextItem(rule.name, yAxis)
        label.setFont(self.timelineFont)
        label.setPos(-label.boundingRect().width() - 10, (0.5 + i) * Y - label.boundingRect().height()/2)
        i = i + 1

    yArrow = QGraphicsPolygonItem(arrow(), parentItem)
    yArrow.setPos(0, -30)
    yArrow.setRotation(180)
    yArrow.setBrush(QBrush(Qt.black))

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
    generator.setSize(self.scene.itemsBoundingRect().size().toSize())
    painter = QPainter()
    painter.begin(generator)
    self.scene.render(painter)
    painter.end()

  def saveAsImage(self, name):
    image = QImage(self.scene.itemsBoundingRect().size().toSize(), QImage.Format_RGB32)
    image.fill(Qt.white)
    painter = QPainter()
    painter.begin(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)
    self.scene.render(painter)
    painter.end()
    image.save(name)
    
  def convertSvgToEps(self, image_name):
    subprocess.call(['inkscape', '-f', image_name + '.svg', '-A', image_name + '.pdf', '--export-latex', '--export-area-drawing'])
    
  def loadTranscriptionAndGenerateGraphs(self, transitions_file, image_file, latex):
    self.loadFileByName(transitions_file)
    
    colorings = {
      COLOR_STEP : 'step',
      COLOR_PERSON : 'person',
      COLOR_PERSON_GRAYSCALE : 'person_gray',
      COLOR_HYPOTHESIS_CONE : 'hypothesis',
      COLOR_HYPOTHESIS : 'hypothesis_all',
    }
    
    for color_option, name in colorings.items():
      self.scene.clear()
      self.displayTimeline(color_option)
      self.scene.setSceneRect(self.scene.itemsBoundingRect())
      self.saveAsSvg(image_file + '_timeline_' + name + '.svg')
      self.saveAsImage(image_file + '_timeline_' + name + '.jpg')
      if latex:
        self.convertSvgToEps(image_file + '_timeline_' + name)
        
    legends = {
      COLOR_PERSON : 'person',
      COLOR_PERSON_GRAYSCALE : 'person_gray',
    }
        
    for color_option, name in legends.items():
      self.scene.clear()
      self.displayLegend(color_option)
      self.scene.setSceneRect(self.scene.itemsBoundingRect())
      self.saveAsSvg(image_file + '_legend_' + name + '.svg')
      self.saveAsImage(image_file + '_legend_' + name + '.jpg')
      if latex:
        self.convertSvgToEps(image_file + '_legend_' + name)
    
    self.scene.clear()
    self.displayCycle(self._fluxMatrix, True)
    self.scene.setSceneRect(self.scene.itemsBoundingRect())
    self.saveAsSvg(image_file + '_cycle_transitions.svg')
    self.saveAsImage(image_file + '_cycle_transitions.jpg')
    if latex:
      self.convertSvgToEps(image_file + '_cycle_transitions')
    
    self.scene.clear()
    self.displayCycle(self._overlapMatrix, False)
    self.scene.setSceneRect(self.scene.itemsBoundingRect())
    self.saveAsSvg(image_file + '_cycle_overlap.svg')
    self.saveAsImage(image_file + '_cycle_overlap.jpg')
    if latex:
      self.convertSvgToEps(image_file + '_cycle_overlap')
      
    self.scene.clear()
    self.displayExpertivity()
    self.scene.setSceneRect(self.scene.itemsBoundingRect())
    self.saveAsSvg(image_file + '_expertivity.svg')
    self.saveAsImage(image_file + '_expertivity.jpg')
    if latex:
      self.convertSvgToEps(image_file + '_expertivity')
    
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
    if dialog.exec_() == QDialog.Accepted:
      dialog.saveOptions()
      self.displayIsle()
