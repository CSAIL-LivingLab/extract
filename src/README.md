
Current Ingestion
-----------------

```python
raw_data = read_data(<filename>)
tokens = tokenize(raw_data)
logical_data = parse(tokens)
features = featurize(logical_data)
```

NEXT UP
=======

dev: specify possible outputs with regexs
  - `[a-zA-z]` -> alpha
    - uppercase
    - lowercase
    - first letter capitalized
    - mixed case
    - etc...
  - `[0-9]` -> number
    - different classes based on # on digits?
  - `[^a-zA-Z & ^0-9]` -> symbol
    - whitespace?
    - punctuation
    - other...?

hierarchy of possible outputs -> granularity on demand

load sample input (txt)
-----------------------

```python
  def load_data(filname):
    with open(filename, 'r') as f:
      return tokenize(f)

  def split_and_pad(tokens):
    # split by separator (eg. newline for now)
    # scan to find max sequence length
    # add terminating STOP and pad with STOPS to reach uniform length

  def featurize(proto_records):
    # apply transformation function to each x
```

load sample output (csv)
------------------------

IDEAS
=====

db storage: different tables for stages (loaded data, tokenized data, etc..)

generate vocabulary:
  sweep text for common words -> articles, predictors

progressive deepening? eg. continuously calculate more granular results
