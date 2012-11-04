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

class View(QGraphicsView):
  def __init__(self, parent):
    QGraphicsView.__init__(self, parent)
    self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
    self.zoom = 1

  def wheelEvent(self, event):
    self.zoom = self.zoom * pow(2, event.delta() / 480.0)
    if self.zoom < 0.07:
      self.zoom = 0.07
    if self.zoom > 100:
      self.zoom = 100

    self.setTransform(QTransform().scale(self.zoom, self.zoom))
    event.accept()

  def resizeEvent(self, event):
    xScale = event.size().width() / event.oldSize().width()
    yScale = event.size().height() / event.oldSize().height()
    self.zoom = self.zoom * min(xScale, yScale)
    self.setTransform(QTransform().scale(self.zoom, self.zoom))

  def resetView(self):
    xScale = self.contentsRect().width() / self.sceneRect().width()
    yScale = self.contentsRect().height() / self.sceneRect().height()
    self.zoom = min(xScale, yScale)
    self.setTransform(QTransform().scale(self.zoom, self.zoom))
    self.centerOn(self.sceneRect().center())

