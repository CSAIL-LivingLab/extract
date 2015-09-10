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
  folder = sys.argv[1]

  in_f = 'data/{}/input.txt'.format(folder)
  out_f = 'data/{}/output.csv'.format(folder)
  test_f = 'data/{}/test.txt'.format(folder)

  fe = FieldExtractor(observation_types)
  fe.train(in_f, out_f)

  print fe.hmm.start_p
  print fe.hmm.trans_p
  print fe.hmm.emit_p

  print fe.extract(test_f)

