import os
import pickle
import numpy as np
import torch
from typing import Optional

from ml.lstm import LatencyLSTM, SEQ_LEN

ANOMALY_Z_THRESHOLD = 2.5
LSTM_ANOMALY_MULTIPLIER = 1.5


def _load_model(model_path: str, scaler_path: str):
    model = LatencyLSTM()
    model.load_state_dict(torch.load(model_path, weights_only=True))
    model.eval()
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def predict_next(model_path: str, scaler_path: str, recent_latencies: list[float]) -> Optional[float]:
    if len(recent_latencies) < SEQ_LEN:
        return None
    try:
        model, scaler = _load_model(model_path, scaler_path)
        seq = np.array(recent_latencies[-SEQ_LEN:], dtype=np.float32).reshape(-1, 1)
        seq_scaled = scaler.transform(seq)
        x = torch.tensor(seq_scaled, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            pred_scaled = model(x).item()
        pred = scaler.inverse_transform([[pred_scaled]])[0][0]
        return float(max(pred, 0))
    except Exception:
        return None


def predict_future(model_path: str, scaler_path: str, recent_latencies: list[float], steps: int = 30) -> list[float]:
    if len(recent_latencies) < SEQ_LEN:
        return []
    try:
        model, scaler = _load_model(model_path, scaler_path)
        seq = list(recent_latencies[-SEQ_LEN:])
        predictions = []
        for _ in range(steps):
            arr = np.array(seq[-SEQ_LEN:], dtype=np.float32).reshape(-1, 1)
            scaled = scaler.transform(arr)
            x = torch.tensor(scaled, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                p = model(x).item()
            pred = float(max(scaler.inverse_transform([[p]])[0][0], 0))
            predictions.append(pred)
            seq.append(pred)
        return predictions
    except Exception:
        return []


def check_anomaly_lstm(model_path: str, scaler_path: str, recent_latencies: list[float], current: float) -> tuple[bool, float, Optional[float]]:
    predicted = predict_next(model_path, scaler_path, recent_latencies)
    if predicted is None or predicted == 0:
        return False, 0.0, None
    ratio = current / predicted
    if ratio > LSTM_ANOMALY_MULTIPLIER:
        confidence = min(1.0, (ratio - 1.0) / 2.0)
        return True, round(confidence, 3), predicted
    return False, 0.0, predicted


def check_anomaly_zscore(latencies: list[float], current: float) -> tuple[bool, float]:
    if len(latencies) < 10:
        return False, 0.0
    arr = np.array(latencies)
    mean, std = arr.mean(), arr.std()
    if std == 0:
        return False, 0.0
    z = (current - mean) / std
    if z > ANOMALY_Z_THRESHOLD:
        confidence = min(1.0, (z - ANOMALY_Z_THRESHOLD) / 3.0)
        return True, round(confidence, 3)
    return False, 0.0
