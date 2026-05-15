"""
Procedural latency profile generator.
Each synthetic service has a unique personality derived from a seed —
same seed always produces the same service, different seeds never repeat.
"""
import random
import math
from dataclasses import dataclass, field


SERVICE_ARCHETYPES = [
    {
        "name_templates": ["auth-service", "identity-api", "oauth-gateway"],
        "baseline_ms": (20, 60),
        "std_ms": (5, 15),
        "peak_hours": list(range(8, 18)),
        "peak_multiplier": (1.3, 1.8),
        "spike_prob": 0.02,
        "down_prob": 0.001,
    },
    {
        "name_templates": ["payments-api", "billing-service", "stripe-proxy"],
        "baseline_ms": (80, 200),
        "std_ms": (20, 50),
        "peak_hours": list(range(9, 21)),
        "peak_multiplier": (1.5, 2.2),
        "spike_prob": 0.015,
        "down_prob": 0.0005,
    },
    {
        "name_templates": ["data-pipeline", "analytics-service", "reporting-api"],
        "baseline_ms": (150, 400),
        "std_ms": (40, 100),
        "peak_hours": list(range(6, 10)) + list(range(18, 22)),
        "peak_multiplier": (2.0, 3.5),
        "spike_prob": 0.04,
        "down_prob": 0.002,
    },
    {
        "name_templates": ["cdn-edge", "static-assets", "media-service"],
        "baseline_ms": (5, 25),
        "std_ms": (2, 8),
        "peak_hours": list(range(10, 23)),
        "peak_multiplier": (1.1, 1.4),
        "spike_prob": 0.005,
        "down_prob": 0.0002,
    },
    {
        "name_templates": ["search-api", "elastic-proxy", "query-service"],
        "baseline_ms": (30, 120),
        "std_ms": (10, 40),
        "peak_hours": list(range(8, 20)),
        "peak_multiplier": (1.4, 2.0),
        "spike_prob": 0.03,
        "down_prob": 0.001,
    },
]


@dataclass
class ServiceProfile:
    id: int
    name: str
    path: str
    baseline_ms: float
    std_ms: float
    peak_hours: list
    peak_multiplier: float
    spike_prob: float
    down_prob: float
    degradation_schedule: list = field(default_factory=list)


def generate_profiles(count: int = 10, seed: int = 42) -> list[ServiceProfile]:
    rng = random.Random(seed)
    profiles = []

    for i in range(count):
        archetype = SERVICE_ARCHETYPES[i % len(SERVICE_ARCHETYPES)]
        name_template = archetype["name_templates"][i // len(SERVICE_ARCHETYPES) % len(archetype["name_templates"])]
        name = f"{name_template}-{i+1}" if count > len(SERVICE_ARCHETYPES) else name_template

        baseline = rng.uniform(*archetype["baseline_ms"])
        std = rng.uniform(*archetype["std_ms"])
        peak_mult = rng.uniform(*archetype["peak_multiplier"])

        degradation_minutes = []
        for _ in range(rng.randint(0, 3)):
            start = rng.randint(0, 1380)
            duration = rng.randint(5, 30)
            severity = rng.uniform(1.5, 4.0)
            degradation_minutes.append((start, start + duration, severity))

        profiles.append(ServiceProfile(
            id=i,
            name=name,
            path=f"/sim/{name.replace('-', '_')}",
            baseline_ms=baseline,
            std_ms=std,
            peak_hours=archetype["peak_hours"],
            peak_multiplier=peak_mult,
            spike_prob=archetype["spike_prob"],
            down_prob=archetype["down_prob"],
            degradation_schedule=degradation_minutes,
        ))

    return profiles
