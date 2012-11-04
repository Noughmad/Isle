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