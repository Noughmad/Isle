from PyQt4.QtCore import QSettings

def calculateExpertivity(fluxMatrix, weights):
  R = len(fluxMatrix)
  allTransitions = sum(sum(row) for row in fluxMatrix)
  
  e = 0
  for i in range(R):
    for j in range(R):
      if i != j:
        e += fluxMatrix[i][j] * weights[i][j]
  e = float(e) / float(allTransitions)
  return e

def loadWeights(R):
  matrix = [[0 for i in range(R)] for j in range(R)]
  
  s = QSettings()
  s.beginGroup('Expertivity')
  for i in range(R):
    s.beginGroup('Row%d' % i)
    for j in range(R):
      if j != i:
        matrix[i][j] = s.value('Column%d' % j, 0, float)
    s.endGroup()
  s.endGroup()
  return matrix