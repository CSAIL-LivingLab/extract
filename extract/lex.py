import re

class Lexer:

  @staticmethod
  def pad(TX):
    for tx in TX:
      tx.append(Token.stop())

    longest = 0
    for tx in TX:
      if len(tx) > longest:
        longest = len(tx)

    for tx in TX:
      pad_length = longest - len(tx) + 1
      tx.extend([Token.stop()] * pad_length)
    return TX

  def __init__(self, types, unk=True):
    self.types = types
    if unk:
      self.unk = 'unk'

  def tokenize(self, text):
    tokens = []
    i = 0
    while i < len(text):
      match = None
      for typ in self.types:
        match = re.match(self.types[typ], text[i:])
        if match:
          tokens.append(Token(typ, match.group()))
          i += match.end()
          break
      if not match:
        if self.unk:
          # TODO extend unk to cover text until reaching a search result for one of the types
          tokens.append(Token.unknown())
          i += 1
        else:
          raise ValueError('{} did not match any types. Could not tokenize'.format(text[i:]))
    return tokens

  def tokenize_all(self, text):
    if type(text) == str or type(text) == unicode:
      tokens_list = self.tokenize(text)
      return tokens_list
    elif type(text) == list or type(text) == tuple:
      tokens_list = []
      for subtext in text:
        tokens_list.append(self.tokenize_all(subtext))
      return tokens_list
    else:
      raise TypeError('Unrecognized type: ' + str(type(text)))

class Token:

  def __init__(self, typ, string):
    self.typ = typ
    self.string = string
    self.stop = False
    self.unk = False

  @staticmethod
  def stop():
    stop_token = Token('STOP', None)
    stop_token.stop = True
    return stop_token

  @staticmethod
  def unknown():
    unk_token = Token('unk', None)
    unk_token.unk = True
    return unk_token

  def __eq__(self, other):
    return type(self) == type(other) and self.__dict__ == other.__dict__

  def __repr__(self):
    if self.string:
      return "<{} {}>".format(repr(self.string)[1:-1], self.typ)
    else:
      return "<{}>".format(self.typ)
