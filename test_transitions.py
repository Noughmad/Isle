import unittest
import chardet
import re

from lib import transitions, rules, parser

def parseTime(time):
  match = re.search('(\d+)[\.:](\d+)', time)
  if match:
    return 60 * int(match.group(1)) + int(match.group(2))
  else:
    return 0

def fixActionTimes(actions):
  for a in actions:
    a.start = parseTime(a.startText)
    a.end = parseTime(a.endText)
    
def expected():
  R = 7
  matrix = [[0 for i in range(R)] for i in range(R)]
  matrix[0][1] = 1
  matrix[0][2] = 1
  matrix[1][1] = 1
  
  matrix[1][3] = 1
  matrix[2][3] = 1
  
  matrix[2][1] = 1
  
  matrix[3][4] = 1
  
  matrix[4][5] = 1
  
  matrix[4][0] = 1
  matrix[5][0] = 1
  
  matrix[5][6] = 1
  matrix[0][6] = 1
  
  return matrix
  
def loadFile(name):
  p = parser.Parser()
  with open("test/" + name + ".html", 'rb') as f:
    content = f.read()
    encoding = chardet.detect(content)['encoding']
    
    p.actions = []
    p.feed(content.decode(encoding))
    fixActionTimes(p.actions)
    
  R = []
  for step in ["Observation", "Patterns", "Multiple Representations", "Analysis", "Design", "Testing", "Judgment"]:
    r = rules.Rules()
    r.name = step
    r.rules = [step]
    R.append(r)
    
  return p.actions, R

class TestTransitions(unittest.TestCase):
  
  def test_flux(self):
    (actions, rules) = loadFile("transcription_vzorec")
    actual = transitions.fluxMatrix(actions, rules)
    
    self.assertEqual(actual, expected())
    
  def test_intermezzo(self):
    (actions, rules) = loadFile("transcription_vzorec2")
    actual = transitions.fluxMatrix(actions, rules)
    
    self.assertEqual(actual, expected())

if __name__ == '__main__':
  unittest.main()
    
