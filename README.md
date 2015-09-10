Xtract
======
Extracting fields from semi-structured data

Install
-------
Installation via `pip`
```bash
git clone https://github.com/pcattori/extract.git
cd extract
pip install -r requirements.txt
```

Run
---

```bash
cd extract
python run.py <dataset>
```

Where `<dataset>` is a directory within the `data` directory with the structure:

- `<dataset>`
  - `input.txt`
  - `output.csv`
  - `test.txt`

NB: example outputs specified as CSV files with headers. Look at `data/hadoop/` and `data/tomcat/` for examples of properly structured datasets

API
---

```python
fe = FieldExtractor(observation_types)
fe.train('input.txt', 'output.csv')
fe.extract('test.txt')
```

TODO
----
- probability thresholds for fields/records (ie. if viterbi probability is too low, don't extract from this line of text)
- unsupervised learning via baum-welch to learn the token types (this could indirectly fix the 'multiple fields clashing' bug)
- type hierarchy and progressive deepening
- submodels for fields
- smoothing
- streaming pipeline
- db as storage
- detecting field separators via language modeling
  - detecting record separators in the same way

BUGS
----
- Fix issue with multiple fields corresponding to same format/structure (eg. src and dst ip addresses)
