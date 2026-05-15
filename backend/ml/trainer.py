import os
import pickle
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler

from ml.lstm import LatencyLSTM, SEQ_LEN

MODELS_DIR = "models"
EPOCHS = 50
BATCH_SIZE = 32
LR = 0.001


def _ensure_dir():
    os.makedirs(MODELS_DIR, exist_ok=True)


def build_sequences(data: np.ndarray, seq_len: int):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i : i + seq_len])
        y.append(data[i + seq_len])
    return np.array(X), np.array(y)


def train_model(endpoint_id: str, latencies: list[float]) -> tuple[str, str]:
    _ensure_dir()

    data = np.array(latencies, dtype=np.float32).reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data)

    X, y = build_sequences(scaled, SEQ_LEN)
    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.float32)

    dataset = TensorDataset(X_t, y_t)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    model = LatencyLSTM()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.MSELoss()

    model.train()
    for _ in range(EPOCHS):
        for xb, yb in loader:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

    model_path = os.path.join(MODELS_DIR, f"{endpoint_id}.pt")
    scaler_path = os.path.join(MODELS_DIR, f"{endpoint_id}_scaler.pkl")

    torch.save(model.state_dict(), model_path)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    return model_path, scaler_path
