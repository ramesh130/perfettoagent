# gpt-5.6-luna, effort high, metric expected

10 planted cases and 0 clean pairs, 3 runs each (30 runs, 0 ended in an error). Provider: openai.

| Rate | Overall | Lowest run | Highest run |
|---|---:|---:|---:|
| Detection | 100% (30/30) | 100% | 100% |
| Attribution | 100% (30/30) | 100% | 100% |
| False positives | – (0/0) | – | – |
| Citation validity | 100% (254/255) | 99% | 100% |

Lowest and highest are the rate over one repetition of every case: the spread, not the best run. The model's confidence is never scored.

## Cases

| Case | Expected | Verdicts | Detected | Attributed | False positive | Flipped |
|---|---|---|---|---|---|---|
| `275adbfb` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `2d80ed28` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `3f05432d` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `462439ff` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `68629563` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `69dc18c7` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `ba4d10bb` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `c89d5055` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `e3a281bb` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |
| `f21c443c` | regression | regression, regression, regression | 3/3 | 3/3 | – |  |

Cache reads from the second run on: 20 of 20 runs read cached tokens.

## Cost

$0.7821 in all; per run $0.0261, 157 s (from 72 to 513 s).
Tokens per run: 40 input, 249,009 cache read, 36,500 cache write, 9,964 output.
