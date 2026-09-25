# gpt-5.6-luna, effort xhigh, metric auto

10 planted cases and 10 clean pairs, 3 runs each (60 runs, 0 ended in an error). Provider: openai.

| Rate | Overall | Lowest run | Highest run |
|---|---:|---:|---:|
| Detection | 93% (28/30) | 80% | 100% |
| Attribution | 100% (28/28) | 100% | 100% |
| False positives | 10% (3/30) | 0% | 20% |
| Citation validity | 96% (603/627) | 94% | 98% |

Lowest and highest are the rate over one repetition of every case: the spread, not the best run. The model's confidence is never scored.

## Cases

| Case | Expected | Verdicts | Detected | Attributed | False positive | Flipped |
|---|---|---|---|---|---|---|
| `275adbfb` | regression | regression, regression, regression | 2/3 | 2/3 | – | yes |
| `2d80ed28` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `33677800` | no_regression | inconclusive, no_regression, inconclusive | – | – | 0/3 | yes |
| `3f05432d` | regression | regression, regression, regression | 2/3 | 2/3 | – | yes |
| `462439ff` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `538c24e3` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `571fe43e` | no_regression | inconclusive, inconclusive, inconclusive | – | – | 0/3 |  |
| `65f39dfe` | no_regression | regression, inconclusive, inconclusive | – | – | 1/3 | yes |
| `68629563` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `69dc18c7` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `9a0b7cd0` | no_regression | no_regression, inconclusive, inconclusive | – | – | 0/3 | yes |
| `b021c1fb` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `ba4d10bb` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `c69ee38f` | no_regression | no_regression, inconclusive, no_regression | – | – | 0/3 | yes |
| `c89d5055` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `d18a09bc` | no_regression | regression, inconclusive, regression | – | – | 2/3 | yes |
| `e04aeae9` | no_regression | inconclusive, no_regression, no_regression | – | – | 0/3 | yes |
| `e3a281bb` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `f21c443c` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `f37266c8` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |

Cache reads from the second run on: 40 of 40 runs read cached tokens.

## Cost

$2.6475 in all; per run $0.0441, 319 s (from 142 to 816 s).
Tokens per run: 47 input, 457,635 cache read, 55,667 cache write, 17,538 output.
