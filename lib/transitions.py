def getCategories(action, rules):
  cat = []
  i = 0
  for r in rules:
    if any(r.match(s) for s in action.steps):
      cat.append(i)
    i = i + 1
  return cat

def addToMatrix(matrix, one, other, rules, bidirectional=False):
  for cc in getCategories(one, rules):
    for nc in getCategories(other, rules):
      matrix[cc][nc] += 1
      if bidirectional:
        matrix[nc][cc] += 1
      
def fluxMatrix(actions, rules):
  R = rules
  n = len(R)
  matrix = [[0 for r in R] for s in R]
  
  for currentAction in actions:
    
    hasOverlap = False
    
    for previousAction in actions:
      
      if currentAction.start <= previousAction.end and currentAction.start > previousAction.start:
        hasOverlap = True
        addToMatrix(matrix, previousAction, currentAction, rules)
        
    if not hasOverlap:
      lastActions = []
      lastTime = 0
      
      for previousAction in actions:
        if previousAction.end <= currentAction.start and getCategories(previousAction, rules):
          if previousAction.end > lastTime and previousAction.end:
            lastTime = previousAction.end
            lastActions = [previousAction];
          elif previousAction.end == lastTime:
            lastActions.append(previousAction);

      for lastAction in lastActions:
        addToMatrix(matrix, lastAction, currentAction, rules)
  return matrix

def overlapMatrix(actions, rules):
  R = rules
  n = len(R)
  matrix = [[0 for r in R] for s in R]
  
  for action in actions:
    cat = getCategories(action, rules)
    if len(cat) > 1:
      addToMatrix(matrix, action, action, rules)
  
  for i in range(len(actions)):
    currentAction = actions[i]
    for j in range(i):
      previousAction = actions[j]
      if currentAction.start < previousAction.end and currentAction.end > previousAction.start:
        addToMatrix(matrix, previousAction, currentAction, rules, bidirectional=True)
  
  return matrix