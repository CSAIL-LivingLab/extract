# TODO numpy?
# TODO ascii string.printable? or unicode aware?

def read_data(filename):
  raw_data = []
  with open(filename, 'r') as f:
    for line in f:
      raw_data.append(line)
  return ''.join(raw_data)

def tokenize(raw_data):
  tokens = []
  token = None
  for char in raw_data:
    # start new token
    if not token:
      token = Token(char)
      continue
    # build on current number token
    if char.isdigit() and token.typ() == Token.NUMBER:
      token.append(char)
    # build on current alpha token
    elif char.isalpha() and token.typ() == Token.ALPHA:
        token.append(char)
    # finish current token, and start a new one
    else:
      tokens.append(token)
      token = Token(char)
  # tack on last token
  if token:
    tokens.append(token)
  return tokens

def parse_data(tokens):
  logical_data = []
  x = []
  for token in tokens:
    # split on newlines
    if token.string == '\n':
      logical_data.append(x)
      x = []
    else:
      x.append(token)
  return logical_data

def featurize(logical_data):
  features = []
  for x in logical_data:
    feature_vector = [token.typ_str() for token in x]
    feature_vector.append('STOP')
    features.append(feature_vector)
  return features

class Token:
  STOP = 0
  NUMBER = 1
  ALPHA = 2
  SYMBOL = 3

  typ2str = {
    STOP: 'end',
    NUMBER: 'num',
    ALPHA: 'abc',
    SYMBOL: 'sym'
  }

  def __init__(self, string):
    self.string = string
    self.stop = False

  @staticmethod
  def stop():
    stop_token = Token(None)
    stop_token.stop = True
    return stop_token

  def typ(self):
    if self.stop:
      return Token.STOP
    elif self.string.isdigit():
      return Token.NUMBER
    elif self.string.isalpha():
      return Token.ALPHA
    else:
      return Token.SYMBOL

  def typ_str(self):
    return Token.typ2str[self.typ()]

  def append(self, char):
    self.string += char

  def __eq__(self, other):
    return self.string == other.string

  def __repr__(self):
    return "<{} {}>".format(repr(self.string)[1:-1], self.typ_str())
