import csv
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

def load_data(filename):
  raw_data = read_data(filename)
  return tokenize(raw_data)

def separate(tokens):
  TX = []
  tx = []
  for token in tokens:
    if token.string == '\n': # separator
      TX.append(tx)
      tx = []
    else:
      tx.append(token)
  if tx:
    TX.append(tx)
  return TX

def pad(TX):
  for tx in TX:
    tx.append(Token.stop())

  longest = 0
  for tx in TX:
    if len(tx) > longest:
      longest = len(tx)

  for tx in TX:
    pad_length = longest - len(tx)
    tx.extend([Token.stop()] * pad_length)

def parse_data(tokens):
  TX = separate(tokens)
  pad(TX)
  return TX

def featurize(TX, phi):
  X = []
  for tx in TX:
    x = [phi(token) for token in tx]
    X.append(x)
  return X

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
    return self.string == other.string and self.stop == other.stop

  def __repr__(self):
    return "<{} {}>".format(repr(self.string)[1:-1], self.typ_str())

# labeling
##########

def load_extractions(filename):
  Te = []
  with open(filename, 'rb') as extract_csv:
    extract_table = csv.reader(extract_csv, skipinitialspace=True, delimiter=',', quotechar='"')
    for row in extract_table:
      extraction = []
      for item in row:
        extraction.append(tokenize(item))
      Te.append(extraction)
  return Te

def examples2labels(Tx, Te):
  Y = []
  print Tx
  print Te
  assert len(Tx) == len(Te)
  for i in range(len(Tx)):
    x_i = Tx[i]
    e_i = Te[i]
    Y.append(labels(x_i, e_i))
  return Y

def labels(x, e):
  matches = ordered_matches(x, e)
  garbage = len(matches) + 1
  labels = [garbage]*len(x)

  for i in range(len(matches)):
    index = matches[i]
    pattern = e[i]
    if pattern:
      replace(labels, range(index, index+len(pattern)), i + 1)

  for i in range(len(labels)):
    if x[i] == Token.stop():
      replace(labels, range(i, len(labels)), 0)
      break
  return labels

def replace(l, indices, value):
  for index in indices:
    l[index] = value

def ordered_matches(x, patterns):
  i = 0
  matches = []
  for pattern in patterns:
    at = next_match(x, pattern, i)
    i = at + len(pattern)
    matches.append(at)
  return matches

def next_match(x, pattern, start):
  i = start
  while i <= len(x) - len(pattern):
    if x[i:i + len(pattern)] == pattern:
      return i
    i += 1
  return -1
