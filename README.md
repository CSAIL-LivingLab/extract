Hidden Markov Models for my thesis

```python
```

Pipeline
--------
1. Parse raw training data into tokens
  ```python
  # each T. is a matrix of tokens
  Tx = parse_observations('input.txt')
  Te = parse_extraction('output.csv')
  ```
2. transform tokens into features
  ```python
  X = phi(Tx)
  Y = labels(Tx, Te)
  # internally: matches = sequence_matches(Tx, Te)
  ```

3.  learn from features
  ```python
  supervised_learn(X,Y)
  ```

4. run on real data
  ```python
  Tx = parse_observations('test.txt')
  X = phi(X)
  viterbi(X)
  ```

API
---

```python
fe = FieldExtractor()
fe.train('input.txt', 'output.csv')
fe.run('test.txt')
```
