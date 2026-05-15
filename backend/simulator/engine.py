"""
Synthetic latency engine — generates realistic latency values procedurally.
No hardcoded data. Every value is computed from the service profile + current time.
"""
import random
import math
import time
from datetime import datetime
from simulator.profiles import ServiceProfile


def _time_of_day_multiplier(profile: ServiceProfile, hour: int, minute: int) -> float:
    if hour in profile.peak_hours:
        t = (minute / 60.0) * math.pi
        smooth = 0.5 + 0.5 * math.sin(t)
        return 1.0 + (profile.peak_multiplier - 1.0) * smooth
    return 1.0


def _degradation_multiplier(profile: ServiceProfile, elapsed_minutes: float) -> float:
    for start, end, severity in profile.degradation_schedule:
        if start <= elapsed_minutes <= end:
            progress = (elapsed_minutes - start) / max(end - start, 1)
            ramp = math.sin(progress * math.pi)
            return 1.0 + (severity - 1.0) * ramp
    return 1.0


def _weekly_pattern(hour: int, weekday: int) -> float:
    if weekday >= 5:
        return 0.6
    return 1.0


def generate_latency(profile: ServiceProfile, rng: random.Random, elapsed_minutes: float) -> tuple[float, bool]:
    now = datetime.utcnow()
    hour, minute, weekday = now.hour, now.minute, now.weekday()

    if rng.random() < profile.down_prob:
        return None, False

    tod = _time_of_day_multiplier(profile, hour, minute)
    deg = _degradation_multiplier(profile, elapsed_minutes)
    weekly = _weekly_pattern(hour, weekday)

    effective_baseline = profile.baseline_ms * tod * deg * weekly
    effective_std = profile.std_ms * (0.5 + 0.5 * tod)

    latency = max(1.0, rng.gauss(effective_baseline, effective_std))

    if rng.random() < profile.spike_prob:
        spike_mag = rng.uniform(3.0, 10.0)
        latency *= spike_mag

    noise = rng.gauss(0, effective_std * 0.1)
    latency = max(1.0, latency + noise)

    return round(latency, 2), True
