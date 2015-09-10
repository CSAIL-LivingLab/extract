Hidden Markov Models for my thesis

```python
```

Pipeline
--------
  ```python
  def phi(...):
    ...

  Ti = load_txt('input.txt')
  To = load_csv('output.csv')
  X = featurize(Ti, phi)
  Y = labels(Ti, To)
  ```

API
---

```python
fe = FieldExtractor()
fe.train('input.txt', 'output.csv')
fe.run('test.txt')
```
