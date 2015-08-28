Ingestion
---------

```python
raw_data = read_data(<filename>)
tokens = tokenize(raw_data)
logical_data = parse(tokens)
features = featurize(logical_data)
```
