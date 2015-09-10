DeepX
=====
Extracting fields from semi-structured data

Run
---
To run with the default Hadoop Log data set:
```bash
python run.py
```

To run on specific data set:
```bash
python run.py <input-example> <output-example> <test-data>
```

API
---

```python
fe = FieldExtractor(observation_types)
fe.train('input.txt', 'output.csv')
fe.extract('test.txt')
```

TODO
----
- unsupervised learning via baum-welch to learn the token types (this could indirectly fix the 'multiple fields clashing' bug)
- type hierarchy and progressive deepening
- smoothing
- streaming pipeline
- db as storage

BUGS
----
- Fix issue where extractor crashes when a token type encounter in the test data was not present in the training data
- Fix issue with multiple fields corresponding to same format/structure (eg. src and dst ip addresses)
