# gpt-5.6-luna, effort medium, metric auto

10 planted cases and 10 clean pairs, 3 runs each (60 runs, 0 ended in an error). Provider: openai.

| Rate | Overall | Lowest run | Highest run |
|---|---:|---:|---:|
| Detection | 80% (24/30) | 70% | 100% |
| Attribution | 92% (22/24) | 86% | 100% |
| False positives | 20% (6/30) | 20% | 20% |
| Citation validity | 92% (379/414) | 90% | 93% |

Lowest and highest are the rate over one repetition of every case: the spread, not the best run. The model's confidence is never scored.

## Cases

| Case | Expected | Verdicts | Detected | Attributed | False positive | Flipped |
|---|---|---|---|---|---|---|
| `275adbfb` | regression | regression, regression, regression | 1/3 | 1/3 | – | yes |
| `2d80ed28` | regression | inconclusive, regression, regression | 2/3 | 2/3 | – | yes |
| `33677800` | no_regression | inconclusive, inconclusive, no_regression | – | – | 0/3 | yes |
| `3f05432d` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `462439ff` | regression | regression, regression, regression | 3/3 | 2/3 | – | yes |
| `538c24e3` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `571fe43e` | no_regression | inconclusive, no_regression, inconclusive | – | – | 0/3 | yes |
| `65f39dfe` | no_regression | regression, regression, regression | – | – | 3/3 |  |
| `68629563` | regression | regression, regression, regression | 1/3 | 1/3 | – | yes |
| `69dc18c7` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `9a0b7cd0` | no_regression | no_regression, no_regression, inconclusive | – | – | 0/3 | yes |
| `b021c1fb` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `ba4d10bb` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `c69ee38f` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `c89d5055` | regression | regression, regression, regression | 2/3 | 2/3 | – | yes |
| `d18a09bc` | no_regression | regression, regression, regression | – | – | 3/3 |  |
| `e04aeae9` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `e3a281bb` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `f21c443c` | regression | regression, regression, regression | 3/3 | 2/3 | – | yes |
| `f37266c8` | no_regression | inconclusive, no_regression, no_regression | – | – | 0/3 | yes |

Cache reads from the second run on: 40 of 40 runs read cached tokens.

## Cost

$0.8023 in all; per run $0.0134, 145 s (from 42 to 546 s).
Tokens per run: 24 input, 88,161 cache read, 23,017 cache write, 4,875 output.
