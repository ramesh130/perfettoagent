# gpt-5.6-luna, effort high, metric auto

5 planted cases and 5 clean pairs, 3 runs each (30 runs, 0 ended in an error). Provider: openai.

| Rate | Overall | Lowest run | Highest run |
|---|---:|---:|---:|
| Detection | 93% (14/15) | 80% | 100% |
| Attribution | 100% (14/14) | 100% | 100% |
| False positives | 33% (5/15) | 20% | 40% |
| Citation validity | 93% (240/257) | 90% | 99% |

Lowest and highest are the rate over one repetition of every case: the spread, not the best run. The model's confidence is never scored.

## Cases

| Case | Expected | Verdicts | Detected | Attributed | False positive | Flipped |
|---|---|---|---|---|---|---|
| `275adbfb` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `462439ff` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `571fe43e` | no_regression | inconclusive, inconclusive, regression | – | – | 1/3 | yes |
| `65f39dfe` | no_regression | regression, regression, regression | – | – | 3/3 |  |
| `69dc18c7` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `b021c1fb` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `c69ee38f` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `c89d5055` | regression | regression, regression, regression | 2/3 | 2/3 | – | yes |
| `f21c443c` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `f37266c8` | no_regression | regression, no_regression, no_regression | – | – | 1/3 | yes |

Cache reads from the second run on: 20 of 20 runs read cached tokens.

## Cost

$0.9696 in all; per run $0.0323, 311 s (from 154 to 1009 s).
Tokens per run: 39 input, 339,710 cache read, 47,925 cache write, 11,280 output.
