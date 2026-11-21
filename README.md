# langdeath: Digital Language Death

Code and data for the Digital Language Death project:

- Kornai, András (2013). Digital language death. *PLoS ONE* 8(10).
  https://doi.org/10.1371/journal.pone.0077056
- Ács, Judit, Katalin Pajkossy and András Kornai (2017). Digital vitality of
  Uralic languages. *Acta Linguistica Academica* 64(3):327–345.
- Juhász, Martin and András Kornai (2026). Digital Language Death Revisited
  (DLDR): A Registered Report Protocol. Under review at *PLOS ONE*.
  (The 2025–26 classifier update serves this study.)

## Layout

| Part | Location | Python | Status |
|---|---|---|---|
| Language-vitality classifier | `classification/` | 3.9+ | **maintained** (updated to current pandas/scikit-learn, 2025–26) |
| Data-collection pipeline and database | `ld/`, `parser_aggregator.py`, `load_country_data.py`, `tsv_exporter.py`, Django apps `dld/` and `ml/`, `langdeath/`, `manage.py` | 2.7 | **legacy, unmaintained** (last changed 2017) |

## Installing (classifier)

    pip install .

installs only the classifier's dependencies (numpy, pandas, scikit-learn).
The classifier reads the language database from an SQLite dump (see
`classification/preprocess.py`).

## Legacy pipeline (historical requirements, not installed)

The pipeline that scrapes and aggregates the language data, and the Django
web interface on top of it, were written for Python 2.7 against:

- Django 1.11.18, South 0.8, django-jsonfield
- nltk, plus the Python 2 standard library (`urllib2`, `HTMLParser`, `cPickle`)

These versions have many known security vulnerabilities and are no longer
declared in `setup.py`. Do not deploy the web interface as-is. Running the
pipeline again would require porting it to Python 3 and a current Django
release (Django 1.11 → 4.2 LTS or later, replacing South with Django's
built-in migrations).
