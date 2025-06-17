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

from html.parser import HTMLParser
from lib.action import Action
import re

def parseTime(time):
  # print("Parsing time:", time)
  match = re.search(r'(\d+)[\.:](\d+)[\.:](\d+)', time)
  if match:
    return 60 * 60 * int(match.group(1)) + 60 * int(match.group(2)) + int(match.group(3))
  else:
    match = re.search(r'(\d+)[\.:](\d+)', time)
    if match:
      return 60 * int(match.group(1)) + int(match.group(2))
    else:
      return 0

class Parser(HTMLParser):

  def __init__(self):
    HTMLParser.__init__(self)
    self.timeRe = re.compile(r'(\d{1,2}[\.:]\d\d([\.:]\d\d)?).+?(\d{1,2}[\.:]\d\d([\.:]\d\d)?)')
    self.oneTimeRe = re.compile(r'(\d{1,2}[\.:]\d\d([\.:]\d\d)?)')
    self.dataRe = re.compile(r'(\(.*\))')
    self.talkerRe = re.compile(r'([a-zA-Z]):\s')
    self.phRe = re.compile(r'\[(.+?)\]')
    self.actions = []
    self.action = None
    self.startTime = None
    self.endTime = None
    self.column = 0
    self.firstRow = True
    self.data = ''

  def handle_starttag(self, tag, attrs):
    if tag == 'tr':
      self.column = 0
      if self.firstRow:
        self.firstRow = False
      else:
        self.action = Action()
    if tag == 'td':
      self.column = self.column + 1

  def handle_endtag(self, tag):
    if tag == 'tr':
      if self.action:
        # print("Finished action:", self.action)
        if hasattr(self.action, "startText"):
          self.actions.append(self.action)
        self.action = None
    elif tag == 'td':
      if self.column == 1:
        data = self.data.replace('\n', ' ')
        if self.action:
          match = self.timeRe.search(data)
          if match:
            # print("Time match:", data, match.group(1, 3))
            (self.action.startText, self.action.endText) = match.group(1, 3)
          else:
            # print("Time no match:", data)
            match = self.oneTimeRe.search(data)
            if match:
              self.action.startText = self.action.endText = match.group(1)
      elif self.column == 2:
        if self.action:
          steps = self.dataRe.sub("", self.data)
          phMatches = self.phRe.finditer(self.data)
          for phMatch in phMatches:
            for s in phMatch.group(1).split(','):
              ph = s.strip()
              if ph.startswith('P'):
                if 'H' in ph:
                  hi = ph.index('H')
                  self.action.phenomena.append(int(ph[1:hi]))
                  self.action.hypotheses.append(int(ph[hi+1:]))
                else:
                  self.action.phenomena.append(int(ph[1:]))
              elif ph.startswith('H'):
                self.action.hypotheses.append(int(ph[1:]))
              elif ph == 'J':
                self.action.judgment = True
            self.action.phenomena.sort()
            self.action.hypotheses.sort()
            if self.action.hypotheses and not self.action.phenomena:
              self.action.phenomena.append(1)
          if 'judgment' in steps or 'judgement' in steps:
            self.action.judgment = True
          steps = self.phRe.sub("", steps)
          self.action.steps = [s.strip() for s in steps.split(',')]
      elif self.column == 4:
        if self.action:
          lst = []
          talkers = self.talkerRe.search(self.data)
          while talkers:
            lst.append(talkers.group(1))
            talkers = self.talkerRe.search(self.data, talkers.end())
          self.action.talkers = set(lst)
      self.data = ''

  def handle_data(self, data):
    self.data = self.data + data
    
  def get_actions(self, parts):
    total = self.actions[-1].end
    part_size = total / parts
    for p in range(parts):
      yield [a for a in self.actions if a.start <= (p+1) * part_size]
      
  def duration(self):
    return self.actions[-1].end
    
  def fixActionTimes(self):
    offset = -parseTime(self.actions[0].startText)
    for i in range(len(self.actions)):
      s = parseTime(self.actions[i].startText)
      e = parseTime(self.actions[i].endText)
      
      if i > 1 and s + offset < (self.actions[i-1].start - 1800):
        offset = self.actions[i-1].end
        
      self.actions[i].start = s + offset
      self.actions[i].end = e + offset
        
  def feed(self, data):
    HTMLParser.feed(self, data)
    self.fixActionTimes()
