"""The models `diagnose` can run on, their providers, effort levels and prices
(ADR-0020).

A model is runnable only if it has a row here: the row names its provider, the effort
levels it supports, and its USD prices with their source and the date they were
checked. A model with no row, a model named under the wrong provider, or an effort
level the model does not have is refused before any request (`check_model`), so every
run records what it cost at the level it names.

Usage is recorded in one shape for both providers, that of `diagnosis.json`'s
`run.usage` (ADR-0006): `input_tokens` counts only the input that was neither read from
nor written to the cache, as Anthropic reports it. `openai_loop.usage_of` converts
OpenAI's counts, whose `input_tokens` includes both.
"""

# The providers `diagnose` has a loop for (ADR-0020); a third needs its own ADR.
PROVIDERS = ("openai", "anthropic")

# ADR-0020, shipped by #43 (ADR-0023).
DEFAULT_PROVIDER = "openai"

# Each provider's model when `--model` is not given (ADR-0020). No date suffix.
DEFAULT_MODELS = {"openai": "gpt-5.6-luna", "anthropic": "claude-opus-5-5"}

# docs/tech-stack.md: `high` unless a sweep asks for another level.
DEFAULT_EFFORT = "high"

# The levels the eval sweeps (roadmap item 9). A model may list others; `--effort`
# takes any level, and check_model refuses one the model does not list.
SWEPT_EFFORTS = ("low", "medium", "high", "xhigh")

# The usage fields `run.usage` records (ADR-0006), each summed over the run's requests.
USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
)

# USD per million tokens, standard tier, by model id (ADR-0020 "Prices"). `efforts` is
# the levels of the sweep (low, medium, high, xhigh) that the model supports; each maps
# one to one onto the provider's own setting. `long_context` is a second price set for
# a request whose whole input (cached or not) is above `above_input_tokens`.
PRICES = {
    # Anthropic's pricing page, checked 2026-09-24. The cache write is the 5-minute
    # one, the only TTL used; thinking is billed as output.
    # ref: https://platform.claude.com/docs/en/about-claude/pricing
    "claude-opus-5-5": {
        "provider": "anthropic",
        "efforts": ("low", "medium", "high", "xhigh"),
        "usd_per_mtok": {
            "input_tokens": 4.00,
            "output_tokens": 20.00,
            "cache_read_input_tokens": 0.20,
            "cache_creation_input_tokens": 5.00,
        },
        "long_context": None,
    },
    # OpenAI's pricing page and the model's page, checked 2026-09-24. Reasoning tokens
    # are billed as output, and are part of `output_tokens`.
    # ref: https://developers.openai.com/api/docs/pricing
    # ref: https://developers.openai.com/api/docs/models/gpt-5.6-luna
    "gpt-5.6-luna": {
        "provider": "openai",
        "efforts": ("low", "medium", "high", "xhigh"),
        "usd_per_mtok": {
            "input_tokens": 0.20,
            "output_tokens": 1.20,
            "cache_read_input_tokens": 0.02,
            "cache_creation_input_tokens": 0.25,
        },
        "long_context": {
            "above_input_tokens": 272_000,
            "usd_per_mtok": {
                "input_tokens": 0.40,
                "output_tokens": 1.80,
                "cache_read_input_tokens": 0.04,
                "cache_creation_input_tokens": 0.50,
            },
        },
    },
}


class ModelRefused(ValueError):
    """The model, provider and effort cannot run together: no price row, the wrong
    provider, or an effort level the model does not have (ADR-0020)."""


class UnpricedModel(ModelRefused):
    """The model has no row in PRICES, so a run could not record its cost."""


def check_model(provider: str, model: str, effort: str) -> None:
    """Raises ModelRefused unless `model` can run on `provider` at `effort`."""
    if provider not in PROVIDERS:
        raise ModelRefused(f"no provider {provider!r}; one of {', '.join(PROVIDERS)}")
    row = PRICES.get(model)
    if row is None:
        priced = ", ".join(m for m, r in PRICES.items() if r["provider"] == provider)
        raise UnpricedModel(f"no price for {model!r}; priced on {provider}: {priced}")
    if row["provider"] != provider:
        raise ModelRefused(f"{model!r} runs on {row['provider']}, not {provider}")
    if effort not in row["efforts"]:
        raise ModelRefused(
            f"{model!r} has no effort {effort!r}; it has {', '.join(row['efforts'])}"
        )


def usd(model: str, usage: dict) -> float:
    """What one request's `usage` cost on `model`. Per request, not per run: the
    long-context price applies to a request by its own input size."""
    usage = {**dict.fromkeys(USAGE_FIELDS, 0), **usage}
    row = PRICES[model]
    prices = row["usd_per_mtok"]
    long = row["long_context"]
    whole_input = (
        usage["input_tokens"]
        + usage["cache_read_input_tokens"]
        + usage["cache_creation_input_tokens"]
    )
    if long and whole_input > long["above_input_tokens"]:
        prices = long["usd_per_mtok"]
    return sum(usage[f] * prices[f] for f in USAGE_FIELDS) / 1_000_000
