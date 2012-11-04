class Action:
  def __init__(self):
    self.start = None
    self.end = None
    self.steps = []
    self.talkers = set()

  def __repr__(self):
    return "Action [%s - %s]: %s (%s)" % (self.start, self.end, ', '.join(self.steps), ','.join(self.talkers))