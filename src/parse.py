import csv
from lex import Token, Lexer

# read
######

def read_txt(filename):
  raw_data = []
  with open(filename, 'r') as f:
    for line in f:
      raw_data.append(line)
  return ''.join(raw_data)

def read_csv(filename):
  with open(filename, 'rb') as f:
    return list(csv.reader(f, skipinitialspace=True, delimiter=',', quotechar='"'))

# parse
#######

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
  return TX

# labeling
##########

# extractions

def labels(Tx, Te):
  Y = []
  assert len(Tx) == len(Te)
  for i in range(len(Tx)):
    x_i = Tx[i]
    e_i = Te[i]
    Y.append(label(x_i, e_i))
  return Y

def label(x, e):
  matches = ordered_matches(x, e)
  labels = [None]*len(x)

  for i in range(len(matches)):
    index = matches[i]
    pattern = e[i]
    if pattern:
      replace(labels, range(index, index+len(pattern)), i)

  for i in range(len(labels)):
    if x[i] == Token.stop():
      replace(labels, range(i, len(labels)), len(matches))
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

# load
######

def load_txt(filename, emission_types):
  text = read_txt(filename)
  lexer = Lexer(emission_types)
  tokens = lexer.tokenize(text)
  Tx = pad(separate(tokens))
  return Tx

def load_csv(filename, emission_types):
  out = read_csv(filename)
  lexer = Lexer(emission_types)
  To = []
  for row in out:
    To.append([lexer.tokenize(item) for item in row])
  return To


def chunk_fields(Z_predict, X):
  C = []
  for i in range(len(Z_predict)):
    z_i = Z_predict[i]
    x_i = X[i]
    chunks = []
    chunk = []
    for t in range(len(z_i)):
      if not chunk or z_i[j] == z_i[j-1]:
        chunk.append(x_i[j])
      else:
        chunks.append(chunk)
        chunk = [x_i[j]]
    chunks.append(chunk)
    C.append(chunks)
  return C
