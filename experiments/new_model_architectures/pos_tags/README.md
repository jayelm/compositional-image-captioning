# POS tags

We annotate all captions with [universal POS tags](https://universaldependencies.org/u/pos/) and interleave the
captions' words with the respective POS tags. The model learns to generate a POS tag and a matching word in a
subsequent timestep.

We train a Bottom-Up and Top-Down attention model on the interleaved data.

## Baseline

### Model trained with held out "brown dog"

Performance on held out test set ("brown dog"):

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|---------------| --------------| --------------| --------------| -------------
1         | 0.007         | 0             | 0             | 0             | N/A
5         | 0.041         | 0.057         | 0.067         | 0             | N/A

Performance on "white car" data:

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------| --------------| --------------| --------------| --------------| -------------
1         | 0.199         | 0.278         | 0.289         | 0.5           | N/A
5         | 0.536         | 0.69          | 0.816         | 0.875         | N/A

### Model trained with held out "white car"

Performance on held out test set ("white car"):

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|---------------| --------------| --------------| --------------| -------------
1         | 0.021         | 0.039         | 0.026         | 0             | N/A
5         | 0.077         | 0.127         | 0.079         | 0             | N/A

Performance on "brown dog" data:

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------| --------------| --------------| --------------| --------------| -------------
1         | 0.079         | 0.126         | 0.2           | 0             | N/A
5         | 0.324         | 0.345         | 0.6           | 1             | N/A

## With GloVe embeddings

### Model trained with held out "brown dog"

Performance on held out test set ("brown dog"):

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|---------------| --------------| --------------| --------------| -------------
1         | 0             | 0             | 0             | 0             | N/A
5         | 0.010         | 0.011         | 0             | 0             | N/A

Performance on "white car" data:

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------| --------------| --------------| --------------| --------------| -------------
1         | 0.096         | 0.159         | 0.184         | 0.125         | N/A
5         | 0.397         | 0.548         | 0.658         | 0.75          | N/A


## Force generation of adjective at second timestep

We force the generation of an adjective by feeding back the POS tag for adjective at the second timestep irrespective
of what the model had generated by itself. This stimulates the model to generate an adjective in the subsequent
timestep.


### Model trained with held out "brown dog"

Performance on held out test set ("brown dog"):

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|---------------| --------------| --------------| --------------| -------------
1         | 0.062         | 0.034         | 0             | 0             | N/A
5         | 0.152         | 0.195         | 0.4           | 1             | N/A

Performance on "white car" data:

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------| --------------| --------------| --------------| --------------| -------------
1         | 0.589         | 0.683         | 0.816         | 1             | N/A
5         | 0.675         | 0.802         | 0.947         | 0.875         | N/A


### Model trained with held out "white car"

Performance on held out test set ("white car"):

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|---------------| --------------| --------------| --------------| -------------
1         | 0.124         | 0.230         | 0.342         | 0.25          | N/A
5         | 0.225         | 0.333         | 0.421         | 0.375         | N/A

Performance on "brown dog" data:

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------| --------------| --------------| --------------| --------------| -------------
1         | 0.569         | 0.667         | 0.867         | 1             | N/A
5         | 0.648         | 0.689         | 0.867         | 1             | N/A


## With GloVe Embeddings and force generation of adjective

### Model trained with held out "brown dog"

Performance on held out test set ("brown dog"):

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|---------------| --------------| --------------| --------------| -------------
1         | 0.093         | 0.126         | 0.333         | 0             | N/A
5         | 0.166         | 0.218         | 0.467         | 0             | N/A

Performance on "white car" data:

Beam size | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------| --------------| --------------| --------------| --------------| -------------
1         | 0.562         | 0.730         | 0.842         | 0.875         | N/A
5         | 0.634         | 0.762         | 0.868         | 0.875         | N/A
