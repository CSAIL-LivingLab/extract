Xtract
======
Extracting fields from semi-structured data

Install
-------
Installation via `pip`
```bash
git clone https://github.com/pcattori/hmm.git
cd hmm
pip install -r requirements.txt
```

Run
---

```bash
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
- unsupervised learning via baum-welch to learn the token types (this could indirectly fix the 'multiple fields clashing' bug)
- type hierarchy and progressive deepening
- smoothing
- streaming pipeline
- db as storage

BUGS
----
- Fix issue with multiple fields corresponding to same format/structure (eg. src and dst ip addresses)
