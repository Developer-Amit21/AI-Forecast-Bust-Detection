"""
Spatio-Temporal Lead-Conditioned U-Net for NWP Forecast Bust & Confidence Prediction.
Consumes multi-channel synoptic forecast fields (PWAT, Z500, MSLP, VORT850, PRECIP)
conditioned on lead time (Day 1 to Day 10) to predict:
  1) Regional Confidence Grid [0.0, 1.0]
  2) Probabilistic Bust Risk Map P(Bust) [0.0, 1.0]
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple

class SinusoidalLeadEmbedding(nn.Module):
    """Encodes discrete lead time (1-10) into continuous embedding vector."""
    def __init__(self, embed_dim: int):
        super().__init__()
        self.embed_dim = embed_dim

    def forward(self, lead_day: torch.Tensor) -> torch.Tensor:
        # lead_day: (B,)
        half_dim = self.embed_dim // 2
        emb_scale = math.log(10000) / (half_dim - 1) if half_dim > 1 else 1.0
        emb = torch.exp(torch.arange(half_dim, dtype=torch.float32, device=lead_day.device) * -emb_scale)
        emb = lead_day.float().unsqueeze(1) * emb.unsqueeze(0)
        emb = torch.cat([torch.sin(emb), torch.cos(emb)], dim=-1)
        if self.embed_dim % 2 == 1:
            emb = F.pad(emb, (0, 1))
        return emb

class DoubleConv(nn.Module):
    """[Conv2d -> BatchNorm2d -> GELU] x 2 with residual connection"""
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.act1 = nn.GELU()
        
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.act2 = nn.GELU()
        
        self.residual = (
            nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
            if in_channels != out_channels
            else nn.Identity()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = self.residual(x)
        out = self.act1(self.bn1(self.conv1(x)))
        out = self.act2(self.bn2(self.conv2(out)))
        return out + res

class SpatialAttention(nn.Module):
    """Lightweight spatial attention module for atmospheric feature saliency."""
    def __init__(self, in_channels: int):
        super().__init__()
        self.conv = nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        attn = torch.cat([avg_out, max_out], dim=1)
        attn = self.sigmoid(self.conv(attn))
        return x * attn

class SpatioTemporalBustUNet(nn.Module):
    """
    Spatio-Temporal Lead-Conditioned U-Net for NWP Bust Detection.
    """
    def __init__(self, in_channels: int = 5, base_channels: int = 32, embed_dim: int = 32):
        super().__init__()
        self.in_channels = in_channels
        self.base_channels = base_channels
        
        # Lead time encoder
        self.lead_embed = SinusoidalLeadEmbedding(embed_dim)
        self.lead_fc = nn.Sequential(
            nn.Linear(embed_dim, base_channels * 2),
            nn.GELU(),
            nn.Linear(base_channels * 2, base_channels * 2)
        )
        
        # Input includes original synoptic channels + explicit normalized lead channel = in_channels + 1
        self.inc = DoubleConv(in_channels + 1, base_channels)
        
        # Downsampling
        self.down1 = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(base_channels, base_channels * 2)
        )
        
        # Bottleneck with Spatial Attention
        self.bottleneck = nn.Sequential(
            DoubleConv(base_channels * 2, base_channels * 4),
            SpatialAttention(base_channels * 4),
            DoubleConv(base_channels * 4, base_channels * 2)
        )
        
        # Upsampling with skip connections
        self.up1 = nn.ConvTranspose2d(base_channels * 2, base_channels * 2, kernel_size=2, stride=2)
        self.conv_up1 = DoubleConv(base_channels * 3, base_channels)
        
        # Refinement block
        self.refine = DoubleConv(base_channels, base_channels)
        
        # Dual Output Heads
        # 1. Regional Confidence: 1.0 (High Skill) to 0.0 (Bust / High Uncertainty)
        self.confidence_head = nn.Sequential(
            nn.Conv2d(base_channels, 16, kernel_size=3, padding=1),
            nn.GELU(),
            nn.Conv2d(16, 1, kernel_size=1),
            nn.Sigmoid()
        )
        
        # 2. Bust Probability: P(Bust) in [0.0, 1.0]
        self.bust_head = nn.Sequential(
            nn.Conv2d(base_channels, 16, kernel_size=3, padding=1),
            nn.GELU(),
            nn.Conv2d(16, 1, kernel_size=1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor, lead_day: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: Synoptic tensor (B, C=5, H, W)
            lead_day: Lead day integer or float tensor (B,) with values in [1, 10]
        Returns:
            confidence: (B, 1, H, W) in [0, 1]
            bust_prob: (B, 1, H, W) in [0, 1]
        """
        B, C, H, W = x.shape
        if lead_day.numel() == 1 and B > 1:
            lead_day = lead_day.repeat(B)
        
        # Concatenate normalized lead day as an auxiliary spatial channel
        lead_norm = (lead_day.float().view(B, 1, 1, 1).expand(B, 1, H, W) - 1.0) / 9.0
        x_in = torch.cat([x, lead_norm], dim=1) # (B, C+1, H, W)
        
        # Encoder
        x1 = self.inc(x_in) # (B, base, H, W)
        x2 = self.down1(x1) # (B, base*2, H//2, W//2)
        
        # Bottleneck + Lead Feature Modulation
        b = self.bottleneck(x2)
        lead_emb = self.lead_fc(self.lead_embed(lead_day)) # (B, base*2)
        b = b + lead_emb.view(B, -1, 1, 1)
        
        # Decoder with Skip connection
        u1 = self.up1(b)
        # Handle odd dimension matching via interpolation if necessary
        if u1.shape[2:] != x1.shape[2:]:
            u1 = F.interpolate(u1, size=x1.shape[2:], mode="bilinear", align_corners=False)
            
        cat1 = torch.cat([u1, x1], dim=1)
        dec = self.conv_up1(cat1)
        dec = self.refine(dec)
        
        # Dual Heads
        confidence = self.confidence_head(dec)
        bust_prob = self.bust_head(dec)
        
        return confidence, bust_prob

def build_model(device: torch.device = torch.device("cpu")) -> SpatioTemporalBustUNet:
    """Instantiates the model on the requested device."""
    model = SpatioTemporalBustUNet(in_channels=5, base_channels=32)
    model.to(device)
    return model
