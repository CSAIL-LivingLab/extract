import re

class Lexer:

  @staticmethod
  def detokenize(tokens):
    return ''.join([token.string for token in tokens])

  def __init__(self, types, unk=True):
    self.types = types
    if unk:
      self.unk = 'unk'

  # TODO match against custom tokens first?
  def tokenize(self, text, stop=True):
    tokens = []
    i = 0
    while i < len(text):
      longest_match = None
      longest_match_typ = None
      for typ in self.types:
        match = re.match(self.types[typ], text[i:])
        if match:
          if longest_match is None or len(match.group()) > len(longest_match.group()):
            longest_match = match
            longest_match_typ = typ
      if longest_match:
        tokens.append(Token(longest_match_typ, longest_match.group()))
        i += longest_match.end()
      elif self.unk:
        # TODO extend unk to cover text until reaching a search result for one of the types
        tokens.append(Token.unknown())
        i += 1
      else:
        raise ValueError('{} did not match any types. Could not tokenize'.format(text[i:]))
    if stop:
      tokens.append(Token.stop())
    return tokens

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
      display_string = repr(self.string)[1:-1]
      if type(self.string) == unicode:
        display_string = repr(self.string)[2:-1]
      return "<{} {}>".format(display_string, self.typ)
    else:
      return "<{}>".format(self.typ)
