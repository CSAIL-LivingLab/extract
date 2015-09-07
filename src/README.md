pipeline
---------

```python
# model
#######

emission_types = {...}

# load
######

in = load_txt('input.txt')
out = load_csv('output.csv')

# lex
#####

lexer = Lexer(emission_types)

## lex input
tokens = lexer.tokenize(in)

## lex output
To = []
for row in len(out):
  To.append([lexer.tokenize(item) for item in row])

# parse
#######

# record break and standardize
Ti = pad(split(tokens))

# numerical
###########

X = featurize(Ti, phi)
X_num, num2x = numerical(X)

# labels
Y = labels(Ti,To)
Y_num, num2y = numerical(Y)

# ML
####

fe = FieldExtractor()

# train
fe.train(X_num, Y_num)

# predict
fe.predict(X_test) # X_test ingested like X_num
```

NEXT UP
=======

hierarchy of possible outputs -> granularity on demand

IDEAS
=====

db storage: different tables for stages (loaded data, tokenized data, etc..)

generate vocabulary:
  sweep text for common words -> articles, predictors

progressive deepening? eg. continuously calculate more granular results
