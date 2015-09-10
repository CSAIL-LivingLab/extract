import sys
from src.extract import FieldExtractor
from src.learn import featurize, numerical
from src.lex import Lexer

def typ(token):
  return token.typ

# model
observation_types = {
  'num': '\d+',
  'abc': '[a-zA-Z]+',
  #'sym': '[-`=[\]\\\\;\',./~!@#$%^&*()_+{}|:"<>?\s]'
  'spc': '\s+',
  #'pnc': '[-`=[\]\\\\;\',./~!@#$%^&*()_+{}|:"<>?]'
  'hyp': '[-]{1}',
  'cln': '[:]{1}',
  'prd': '[.]{1}',
  'pnc': '[`=[\]\\\\;\',/~!@#$%^&*()_+{}|"<>?]'
}

if __name__ == '__main__':
  in_f = 'data/hadoop/input.txt'
  out_f = 'data/hadoop/output.csv'
  test_f = 'data/hadoop/test.txt'
  if len(sys.argv) > 1:
    in_f = sys.argv[1]
  if len(sys.argv) > 2:
    out_f = sys.argv[2]
  if len(sys.argv) > 3:
    test_f = sys.argv[3]

  fe = FieldExtractor(observation_types)
  fe.train(in_f, out_f)

  print fe.hmm.start_p
  print fe.hmm.trans_p
  print fe.hmm.emit_p

  print fe.extract(test_f)

