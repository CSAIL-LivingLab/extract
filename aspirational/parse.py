def load_data(filename):
  with open(filename, 'r') as f:
    return tokenize(f)

def tokenize(stream):
  token = None
  char = stream.read(1)
  while char:
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
      yield token
      token = Token(char)

    char = stream.read(1)

  yield token
