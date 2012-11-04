from html.parser import HTMLParser
from action import Action
import re

class Parser(HTMLParser):

  def __init__(self):
    HTMLParser.__init__(self)
    self.timeRe = re.compile(r'(\d{1,2}\.\d\d).+?(\d{1,2}\.\d\d)')
    self.oneTimeRe = re.compile(r'(\d{1,2}[\.:]\d\d)')
    self.dataRe = re.compile(r'(\(.*\))')
    self.talkerRe = re.compile(r'([a-zA-Z]):\s')
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
        print(self.action)
        self.actions.append(self.action)
        self.action = None
    elif tag == 'td':
      if self.column == 1:
        if self.action:
          print(self.data)
          match = self.timeRe.search(self.data)
          if match:
            (self.action.start, self.action.end) = match.group(1, 2)
          else:
            match = self.oneTimeRe.search(self.data)
            if match:
              self.action.start = self.action.end = match.group(1)
      elif self.column == 2:
        if self.action:
          steps = self.dataRe.sub("", self.data)
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
