import sys
from src.extract import FieldExtractor
from src.learn import featurize, numerical
from src.lex import Lexer
from src.parse import load_txt, load_csv, pad, separate, labels

def typ(token):
  return token.typ

# model
emission_types = {
  'num': '\d+',
  'abc': '[a-zA-Z]+',
  'sym': '[-`=[\]\\\\;\',./~!@#$%^&*()_+{}|:"<>?\s]'
}

if __name__ == '__main__':
  in_filename = sys.argv[1]
  out_filename = sys.argv[2]

  # load
  ######

  inpt = load_txt(in_filename)
  out = load_csv(out_filename)

  # lex
  #####

  lexer = Lexer(emission_types)

  ## lex input
  tokens = lexer.tokenize(inpt)
  print 'tokens:\n{}'.format(tokens)

  ## lex output
  To = []
  for row in out:
    To.append([lexer.tokenize(item) for item in row])
  print 'lexed out:\n{}'.format(To)

  # parse
  #######

  # record break and standardize
  Ti = pad(separate(tokens))
  print 'parsed in:\n{}'.format(Ti)

  # numerical
  ###########

  X = featurize(Ti, typ)
  print 'X:\n{}'.format(X)
  X_num, x_translator = numerical(X)
  print 'X_num:\n{}'.format(X_num)

  # labels
  Y = labels(Ti,To)
  print 'Y:\n{}'.format(Y)
  Y_num, y_translator = numerical(Y)
  print 'Y_num:\n{}'.format(Y_num)

  # ML
  ####

  fe = FieldExtractor()

  # train
  fe.train(X_num, Y_num)

  print fe.hmm.start_p
  print fe.hmm.trans_p
  print fe.hmm.emit_p

  test_data = load_txt(sys.argv[3])
  tokens_test = lexer.tokenize(test_data)
  Tx_test = pad(separate(tokens_test))
  X_test = featurize(Tx_test, typ)
  X_test_num, _ = numerical(X_test, x_translator)

  # predict
  for x_test_num in X_test_num:
    print fe.extract(x_test_num) # X_test ingested like X_num
