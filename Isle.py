import sys
from mainwindow import MainWindow
from PyQt4.QtGui import QApplication

if __name__ == "__main__":
  app = QApplication(sys.argv)
  mw = MainWindow()
  mw.show()

  if len(sys.argv) > 1:
    mw.loadFileByName(sys.argv[1])
  
  sys.exit(app.exec_())