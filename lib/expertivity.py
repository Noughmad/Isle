def calculateExpertivity(fluxMatrix, weights):
  R = len(fluxMatrix)
  allTransitions = sum(sum(row) for row in fluxMatrix)
  
  e = 0
  for i in range(0, R):
    for j in range(0, R):
      if i != j:
        e += fluxMatrix[i][j] * weights[i][j]
  e = float(e) / float(allTransitions)
  return e
