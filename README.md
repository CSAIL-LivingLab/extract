Hidden Markov Models for my thesis

```python
```

Pipeline
--------
  ```python
  in = load_txt('input.txt')
  out = load_csv('output.csv')
  
  ```

API
---

```python
fe = FieldExtractor()
fe.train('input.txt', 'output.csv')
fe.run('test.txt')
```
