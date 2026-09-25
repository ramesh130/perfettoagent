# gpt-5.6-luna, effort low, metric auto

10 planted cases and 10 clean pairs, 3 runs each (60 runs, 0 ended in an error). Provider: openai.

| Rate | Overall | Lowest run | Highest run |
|---|---:|---:|---:|
| Detection | 73% (22/30) | 70% | 80% |
| Attribution | 91% (20/22) | 86% | 100% |
| False positives | 20% (6/30) | 20% | 20% |
| Citation validity | 96% (347/363) | 92% | 99% |

Lowest and highest are the rate over one repetition of every case: the spread, not the best run. The model's confidence is never scored.

## Cases

| Case | Expected | Verdicts | Detected | Attributed | False positive | Flipped |
|---|---|---|---|---|---|---|
| `275adbfb` | regression | regression, regression, regression | 0/3 | 0/3 | – |  |
| `2d80ed28` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `33677800` | no_regression | no_regression, no_regression, inconclusive | – | – | 0/3 | yes |
| `3f05432d` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `462439ff` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `538c24e3` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `571fe43e` | no_regression | inconclusive, no_regression, no_regression | – | – | 0/3 | yes |
| `65f39dfe` | no_regression | regression, regression, regression | – | – | 3/3 |  |
| `68629563` | regression | regression, regression, regression | 1/3 | 1/3 | – | yes |
| `69dc18c7` | regression | no_regression, regression, no_regression | 0/3 | 0/3 | – | yes |
| `9a0b7cd0` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `b021c1fb` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `ba4d10bb` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `c69ee38f` | no_regression | no_regression, no_regression, no_regression | – | – | 0/3 |  |
| `c89d5055` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `d18a09bc` | no_regression | regression, regression, regression | – | – | 3/3 |  |
| `e04aeae9` | no_regression | no_regression, no_regression, inconclusive | – | – | 0/3 | yes |
| `e3a281bb` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `f21c443c` | regression | regression, regression, regression | 3/3 | 1/3 | – | yes |
| `f37266c8` | no_regression | no_regression, inconclusive, no_regression | – | – | 0/3 | yes |

Cache reads from the second run on: 40 of 40 runs read cached tokens.

## Cost

$0.4417 in all; per run $0.0074, 84 s (from 25 to 449 s).
Tokens per run: 17 input, 38,168 cache read, 14,379 cache write, 2,500 output.
