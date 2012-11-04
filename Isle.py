import sys
from parser import Parser

if __name__ == "__main__":
  categories = [
    'Observation',
    'Formulation of hypethesis',
    'Prediction',
    'Testing experiment',
    'Recognizing patterns',
    'Collecting data',
  ]

  parser = Parser(categories)
  with open(sys.argv[1], 'rt') as f:
    parser.feed(f.read())

