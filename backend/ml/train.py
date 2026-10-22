"""
Training Pipeline for NWP Forecast Bust & Confidence Spatio-Temporal U-Net.
Optimizes composite loss (BCE on bust probability + MSE on continuous confidence)
and saves checkpoint to data/model_weights.pt.
"""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
from typing import List, Tuple

from backend.app.core.config import settings
from backend.ml.data_generator import WeatherDataGenerator
from backend.ml.model import SpatioTemporalBustUNet

class SynopticDataset(Dataset):
    def __init__(self, samples: List[Tuple[np.ndarray, int, np.ndarray, np.ndarray]]):
        """
        Each sample is:
          x: (5, H, W) normalized
          lead_day: int
          confidence_gt: (1, H, W)
          bust_gt: (1, H, W)
        """
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        x, lead_day, conf_gt, bust_gt = self.samples[idx]
        return (
            torch.tensor(x, dtype=torch.float32),
            torch.tensor(lead_day, dtype=torch.long),
            torch.tensor(conf_gt, dtype=torch.float32),
            torch.tensor(bust_gt, dtype=torch.float32)
        )

def build_training_dataset(num_seeds: int = 4) -> SynopticDataset:
    """Generates synthetic training samples from varied synoptic seeds and scenarios."""
    scenarios = ["western_disturbance", "monsoon_depression", "monsoon_break", "climatology"]
    samples = []
    
    for s_idx in range(num_seeds):
        gen = WeatherDataGenerator(seed=100 + s_idx)
        for sc in scenarios:
            ds, _ = gen.simulate_scenario(sc)
            for lead in range(1, 11):
                day_idx = lead - 1
                
                # Extract and normalize channels
                ch_arrays = []
                for ch in settings.CHANNELS:
                    raw = ds[f"forecast_{ch}"].values[day_idx]
                    mean = settings.NORM_PARAMS[ch]["mean"]
                    std = settings.NORM_PARAMS[ch]["std"]
                    norm = (raw - mean) / std
                    ch_arrays.append(norm)
                
                x = np.stack(ch_arrays, axis=0) # (5, H, W)
                conf = ds["confidence_ground_truth"].values[day_idx][np.newaxis, ...] # (1, H, W)
                bust = ds["bust_ground_truth"].values[day_idx][np.newaxis, ...] # (1, H, W)
                
                samples.append((x, lead, conf, bust))
                
    return SynopticDataset(samples)

def train_model(
    epochs: int = 12,
    batch_size: int = 8,
    lr: float = 1e-3,
    save_path: Path = settings.MODEL_WEIGHTS_PATH,
    device: torch.device = torch.device("cpu")
):
    print(f"[+] Initializing training dataset on {device}...")
    dataset = build_training_dataset(num_seeds=3)
    train_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    model = SpatioTemporalBustUNet(in_channels=5, base_channels=32).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    bce_loss_fn = nn.BCELoss()
    mse_loss_fn = nn.MSELoss()
    
    model.train()
    print(f"[+] Commencing training ({len(dataset)} samples, {epochs} epochs)...")
    
    for epoch in range(1, epochs + 1):
        epoch_loss = 0.0
        epoch_bce = 0.0
        epoch_mse = 0.0
        
        for batch_x, batch_lead, batch_conf, batch_bust in train_loader:
            batch_x = batch_x.to(device)
            batch_lead = batch_lead.to(device)
            batch_conf = batch_conf.to(device)
            batch_bust = batch_bust.to(device)
            
            optimizer.zero_grad()
            pred_conf, pred_bust = model(batch_x, batch_lead)
            
            loss_bce = bce_loss_fn(pred_bust, batch_bust)
            loss_mse = mse_loss_fn(pred_conf, batch_conf)
            loss = loss_bce + 0.6 * loss_mse
            
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item() * batch_x.size(0)
            epoch_bce += loss_bce.item() * batch_x.size(0)
            epoch_mse += loss_mse.item() * batch_x.size(0)
            
        scheduler.step()
        n = len(dataset)
        print(f"    Epoch {epoch:02d}/{epochs:02d} | Total Loss: {epoch_loss/n:.4f} | BCE(Bust): {epoch_bce/n:.4f} | MSE(Conf): {epoch_mse/n:.4f}")
        
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"[✓] Checkpoint saved successfully to {save_path}")
    return model

if __name__ == "__main__":
    train_model()
