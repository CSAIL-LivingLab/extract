import csv
import sys

# tokenization
##############

class Token():
  STOP = 0
  NUMBER = 1
  ALPHA = 2
  SYMBOL = 3

  typ2str = {
    NUMBER: 'num',
    ALPHA: 'abc',
    SYMBOL: 'sym',
    STOP: 'end'
  }

  def __init__(self, string=None):
    if not string:
      self.string = ''
    else:
      self.string = string

  def __repr__(self):
    typstr = Token.typ2str[self.typ()]
    return "<{} {}>".format(repr(self.string)[1:-1], typstr)

  def __eq__(self, other):
    return self.string == other.string

  def typ(self):
    if not self.string:
      return Token.STOP
    elif self.string.isdigit():
      return Token.NUMBER
    elif self.string.isalpha():
      return Token.ALPHA
    else:
      return Token.SYMBOL

  def append(self, char):
    self.string += char

  def isEmpty(self):
    return len(self.string) == 0

def tokenize(text):
  tokens = []
  token = Token()
  for char in text:

    if char.isdigit():
      if token.isEmpty() or token.typ() == Token.NUMBER:
        token.append(char)
      else:
        tokens.append(token)
        token = Token(char)

    elif char.isalpha():
      if token.isEmpty() or token.typ() == Token.ALPHA:
        token.append(char)
      else:
        tokens.append(token)
        token = Token(char)

    else:
      if not token.isEmpty():
        tokens.append(token)
      token = Token(char)

  if not token.isEmpty():
    tokens.append(token)

  return tokens

# parsing
#########

def parse_data(data_file):
  T = []
  with open(data_file, 'rb') as f:
    for line in f:
      T.append(tokenize(line))
  return T

def parse_labels(label_file):
  Te = []
  with open(label_file, 'rb') as csv_extract:
    extractions = csv.reader(csv_extract, skipinitialspace=True, delimiter=',', quotechar='"')
    for row in extractions:
      extraction_i = []
      for item in row:
        extraction_i.append(tokenize(item))
      Te.append(extraction_i)
  return Te

# sequence matching
###################

def label(seq, patterns):
  matches = sequence_matches(seq, patterns)
  labels = [None]*len(seq)
  for i in range(len(matches)):
    pattern, index = matches[i]
    if pattern:
      labels[index:index+len(pattern)] = [i] * len(pattern)
  return labels

def sequence_match(pattern, seq, start):
  i = start
  while i <= len(seq) - len(pattern):
    if seq[i:i + len(pattern)] == pattern:
      return True, i
    i += 1
  return False, False

def sequence_matches(seq, patterns):
  i = 0
  matches = []
  for pattern in patterns:
    if pattern:
      found, at = sequence_match(pattern, seq, i)
      i = at + len(pattern)
      if found:
        matches.append((pattern, at))
      else:
        break
  return matches

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print 'no file provided... exiting'
    quit()
  with open(sys.argv[1]) as f:
    print tokenize(f.read())
