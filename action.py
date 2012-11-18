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

class Action:
  def __init__(self):
    self.start = None
    self.end = None
    self.steps = []
    self.talkers = set()
    self.hypotheses = set()
    self.phenomena = set()

  def __repr__(self):
    return "Action [%s - %s]: %s (%s)" % (self.start, self.end, ', '.join(self.steps), ','.join(self.talkers))