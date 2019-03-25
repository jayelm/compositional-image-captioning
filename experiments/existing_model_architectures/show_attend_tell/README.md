# Experiments

## 1. Generalisation Capabilities

**Research Question: How well do Multimodal Neural Language Models (MNLMs) generalise to unseen
Adjective-Noun (Adj-N) pairs?**

All images of the COCO dataset were annotated with information about how often a specific adjective-noun pair
combination occurs in the corresponding captions. 

Subsets of the COCO training set were created by removing all samples where a specific adjective-noun pair occurs at
least once in the caption. For each of the training sets, a model was trained. 

For the evaluation, data from the COCO validation set was annotated in the same way. This time, only samples that where
the adjective-noun pair occurs are added to the test set.

Notes on how to interpret the results:
- "Recall (n>=1)" stands for the recall of the respective adjective noun pair,
where n of the target captions contain the adjective noun pair.
- For a beam size of n, the top n sentences are produced. If at least one of the sentences contains the target
adjective-noun pair, the sample is counted as true positive (i.e. we are calculating the recall@n)

### Show, Attend and Tell

#### Model trained with held out "brown dog"

Performance on held out test set ("brown dog"):

Beam size | BLEU-4 | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|--------| --------------| --------------| --------------| --------------| -------------
1         | 0.255  | 0.003         | 0.011         | 0             | 0             | N/A
5         | 0.275  | 0.024         | 0.046         | 0             | 0             | N/A
10        | 0.276  | 0.024         | 0.034         | 0             | 0             | N/A
50        | 0.278  | 0.089         | 0.092         | 0             | 0             | N/A

Performance on "white car" data:

Beam size | BLEU-4 | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|--------| --------------| --------------| --------------| --------------| -------------
1         | 0.233  | 0.134         | 0.183         | 0.263         | 0.375         | N/A
5         | 0.264  | 0.383         | 0.5           | 0.711         | 0.75          | N/A


#### Model trained with held out "white car"

Performance on held out test set ("white car"):

Beam size | BLEU-4 | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|--------| --------------| --------------| --------------| --------------| -------------
1         | 0.229  | 0.012         | 0.008         | 0             | 0             | N/A
5         | 0.241  | 0.019         | 0.008         | 0             | 0             | N/A

Performance on "brown dog" data:

Beam size | BLEU-4 | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|--------| --------------| --------------| --------------| --------------| -------------
1         | 0.269  | 0.014         | 0.034         | 0.067         | 0             | N/A
5         | 0.317  | 0.328         | 0.471         | 0.8           | 1             | N/A

#### Model trained with held out "big car"

Performance on held out test set ("big car"):

Beam size | BLEU-4 | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|--------| --------------| --------------| --------------| --------------| -------------
1         | 0.217  | 0.012         | 0.016         | 0.038         | 0             | N/A
5         | 0.247  | 0.002         | 0.008         | 0             | 0             | N/A

Performance on "brown dog" data:

Beam size | BLEU-4 | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|--------| --------------| --------------| --------------| --------------| -------------
1         | 0.268  | 0.017         | 0.023         | 0.067         | 0             | N/A
5         | 0.303  | 0.328         | 0.414         | 0.667         | 1             | N/A

Performance on "white car" data:

Beam size | BLEU-4 | Recall (n>=1) | Recall (n>=2) | Recall (n>=3) | Recall (n>=4) | Recall (n>=5)
----------|--------| --------------| --------------| --------------| --------------| -------------
1         | 0.205  | 0.069         | 0.087         | 0.105         | 0.125         | N/A
5         | 0.220  | 0.196         | 0.254         | 0.395         | 0.5           | N/A


The results suggest that the model does not generalise to unseen adjective-noun pairs. The recall for adjective-noun
pairs of a model that was trained on data excluding the pairs is in all cases significantly lower compared to the recall of models that
were trained without the pairs being excluded from the training set.

#### Case studies

To understand why the models are failing to describe the respective adjective-noun pairs, case studies are performed.
We analyse samples where the agreement among the target captions is very high (n >= 4).

The following files contain the visualized attention and the full decoding beam for every timestep for different
samples:
- [brown_dog_1.md](brown_dog_1.md)
- [brown_dog_2.md](brown_dog_2.md)
- [brown_dog_3.md](brown_dog_3.md)
- [white_car_1.md](white_car_1.md)
- [white_car_2.md](white_car_2.md)
- [white_car_3.md](white_car_3.md)

The adjective-noun pair does not occur in any of the case studies' examples. In some cases, the adjective
occurs early in the beam, but then disappears when it would be combined with the noun. In
[white_car_1.md](white_car_1.md) we can see an example where the object has multiple colors, and the model describes
only the color it has seen in relation to the object at training time.

#### Case studies with grayscale images

**Model trained with heldout "white car"**

Captions generated for RGB image:
![RGB Image](brown_dog_rgb_1.png)
```
['a', 'large', 'brown', 'dog', 'sitting', 'on', 'top', 'of', 'a', 'bed']
['a', 'large', 'brown', 'dog', 'laying', 'on', 'a', 'bed']
['a', 'large', 'brown', 'dog', 'sitting', 'on', 'a', 'bed']
['a', 'brown', 'dog', 'laying', 'on', 'a', 'bed', 'in', 'a', 'room']
['a', 'white', 'dog', 'laying', 'on', 'a', 'bed', 'in', 'a', 'room']
```

Captions generated for the same image in grayscale:
![Grayscale Image](brown_dog_gray_1.png)
```
['a', 'dog', 'laying', 'on', 'a', 'bed', 'in', 'a', 'room']
['a', 'dog', 'laying', 'on', 'a', 'bed', 'in', 'a', 'bedroom']
['a', 'dog', 'laying', 'on', 'a', 'bed', 'in', 'a', 'bathroom']
['a', 'dog', 'laying', 'on', 'a', 'bed', 'next', 'to', 'a', 'window']
['a', 'dog', 'is', 'laying', 'on', 'a', 'bed', 'in', 'a', 'room']
```

**Model trained with heldout "brown dog"**

Captions generated for RGB image:
![RGB Image](white_car_rgb_1.png)
```
['a', 'red', 'truck', 'parked', 'in', 'a', 'parking', 'lot']
['a', 'red', 'truck', 'is', 'parked', 'in', 'a', 'parking', 'lot']
['a', 'red', 'truck', 'parked', 'on', 'the', 'side', 'of', 'the', 'road']
['a', 'red', 'truck', 'is', 'parked', 'on', 'the', 'side', 'of', 'the', 'road']
['a', 'red', 'truck', 'parked', 'on', 'the', 'side', 'of', 'a', 'road']
```

Captions generated for the same image in grayscale:
![Grayscale Image](white_car_gray_1.png)
```
['a', 'black', 'and', 'white', 'photo', 'of', 'an', 'old', 'truck']
['a', 'black', 'and', 'white', 'photo', 'of', 'a', 'man', 'on', 'a', 'truck']
['a', 'black', 'and', 'white', 'photo', 'of', 'a', 'truck', 'on', 'a', 'street']
['a', 'black', 'and', 'white', 'photo', 'of', 'a', 'man', 'in', 'a', 'truck']
['a', 'black', 'and', 'white', 'photo', 'of', 'a', 'truck', 'on', 'a', 'road']
```

Captions generated for RGB image:
![RGB Image](white_car_rgb_2.png)
```
['a', 'white', 'truck', 'is', 'driving', 'down', 'the', 'road']
['a', 'white', 'truck', 'driving', 'down', 'a', 'street', 'next', 'to', 'a', 'forest']
['a', 'white', 'truck', 'driving', 'down', 'a', 'street', 'next', 'to', 'a', 'building']
['a', 'white', 'truck', 'driving', 'down', 'a', 'street', 'next', 'to', 'a', 'car']
['a', 'large', 'white', 'truck', 'driving', 'down', 'a', 'street', 'next', 'to', 'a', 'forest']
```

Captions generated for the same image in grayscale:
![Grayscale Image](white_car_gray_2.png)
```
['a', 'black', 'and', 'white', 'photo', 'of', 'a', 'man', 'on', 'a', 'truck']
['a', 'black', 'and', 'white', 'photo', 'of', 'a', 'man', 'and', 'a', 'truck']
['a', 'black', 'and', 'white', 'photo', 'of', 'a', 'truck', 'and', 'a', 'truck']
['a', 'black', 'and', 'white', 'photo', 'of', 'a', 'man', 'in', 'a', 'truck']
['a', 'black', 'and', 'white', 'photo', 'of', 'a', 'man', 'on', 'a', 'truck', 'with', 'a', 'truck']
```

#### Beam Occurrences

**Occurrences of "brown dog"**

Model trained with heldout brown dog:
![Beam Occurrences](beam_occurrences_sat_brown_dog_brown_dog.png)

Model trained with heldout white car:
![Beam Occurrences](beam_occurrences_sat_white_car_brown_dog.png)


**Occurrences of "white car"**

Model trained with heldout white car:
![Beam Occurrences](beam_occurrences_sat_white_car_white_car.png)

Model trained with heldout brown dog:
![Beam Occurrences](beam_occurrences_sat_brown_dog_white_car.png)