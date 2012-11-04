from PyQt4.QtGui import *

class View(QGraphicsView):
  def __init__(self, parent):
    QGraphicsView.__init__(self, parent)
    self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
    self.zoom = 1

  def wheelEvent(self, event):
    self.zoom = self.zoom * pow(2, -event.delta() / 480.0)
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
    xScale = self.sceneRect().width() / self.contentsRect().width()
    yScale = self.sceneRect().height() / self.contentsRect().height()
    self.zoom = min(xScale, yScale)
    self.setTransform(QTransform().scale(self.zoom, self.zoom))
    self.centerOn(self.sceneRect().center())

