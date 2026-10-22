"""
Explainable AI (XAI) Module for NWP Forecast Bust Detection.
Uses Gradient-based Attribution / Integrated Gradients (Captum) to identify
which meteorological variables and spatial synoptic features drive forecast busts.
Generates automated meteorological diagnostic briefings for operational forecasters.
"""
import torch
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from captum.attr import IntegratedGradients, Saliency

from backend.app.core.config import settings

class WeatherXAI:
    def __init__(self, model: torch.nn.Module, device: torch.device = torch.device("cpu")):
        self.model = model
        self.device = device
        self.model.eval()

    def attribute_coordinate(
        self,
        x_tensor: torch.Tensor,
        lead_day: int,
        lat_idx: int,
        lon_idx: int,
        target_head: str = "bust",  # 'bust' or 'confidence'
        method: str = "integrated_gradients",
        n_steps: int = 15
    ) -> Dict[str, Any]:
        """
        Calculates attribution scores for all 5 synoptic variables at a given grid cell.
        
        Args:
            x_tensor: (1, 5, H, W) normalized meteorological input tensor
            lead_day: Forecast lead day (1 to 10)
            lat_idx: Row index corresponding to latitude
            lon_idx: Col index corresponding to longitude
            target_head: 'bust' (explain what causes high bust risk) or 'confidence'
            method: 'integrated_gradients' or 'saliency'
        """
        x_input = x_tensor.clone().detach().to(self.device).requires_grad_(True)
        lead_t = torch.tensor([lead_day], device=self.device)
        
        # Define wrapper function for Captum
        def forward_target(inputs):
            conf, bust = self.model(inputs, lead_t)
            if target_head == "bust":
                # Output target is the bust probability at the specific coordinate
                return bust[:, 0, lat_idx, lon_idx]
            else:
                # Inverse confidence (uncertainty)
                return 1.0 - conf[:, 0, lat_idx, lon_idx]

        # Baseline: zeros or climatological mean
        baseline = torch.zeros_like(x_input)
        
        if method == "integrated_gradients":
            ig = IntegratedGradients(forward_target)
            attributions = ig.attribute(
                x_input,
                baselines=baseline,
                n_steps=n_steps,
                method="gausslegendre"
            )
        else:
            sal = Saliency(forward_target)
            attributions = sal.attribute(x_input)

        # attributions has shape (1, 5, H, W)
        attr_np = attributions.squeeze(0).detach().cpu().numpy() # (5, H, W)
        
        # Calculate local variable impact around the coordinate (using 3x3 local receptive field)
        H, W = attr_np.shape[1], attr_np.shape[2]
        r = 2 # neighborhood radius
        lat_min = max(0, lat_idx - r)
        lat_max = min(H, lat_idx + r + 1)
        lon_min = max(0, lon_idx - r)
        lon_max = min(W, lon_idx + r + 1)
        
        local_crop = np.abs(attr_np[:, lat_min:lat_max, lon_min:lon_max])
        var_importance_raw = np.mean(local_crop, axis=(1, 2)) # (5,)
        
        # Prevent division by zero
        total_imp = np.sum(var_importance_raw)
        if total_imp <= 1e-7:
            var_pct = np.array([20.0, 20.0, 20.0, 20.0, 20.0])
        else:
            var_pct = (var_importance_raw / total_imp) * 100.0

        channel_contributions = {}
        for idx, ch in enumerate(settings.CHANNELS):
            channel_contributions[ch] = {
                "name": settings.CHANNEL_NAMES[ch],
                "percentage": round(float(var_pct[idx]), 1),
                "importance_score": round(float(var_importance_raw[idx]), 4)
            }

        # Spatial importance map: overall magnitude across channels
        spatial_heat = np.mean(np.abs(attr_np), axis=0)
        spatial_heat_norm = (spatial_heat - spatial_heat.min()) / (spatial_heat.max() - spatial_heat.min() + 1e-7)

        # Ranked drivers
        ranked_vars = sorted(
            channel_contributions.items(),
            key=lambda item: item[1]["percentage"],
            reverse=True
        )

        # Generate meteorological briefing
        briefing = self._generate_meteorological_briefing(
            ranked_vars=ranked_vars,
            lead_day=lead_day,
            lat_deg=settings.LAT_MIN + lat_idx * settings.RESOLUTION_DEG,
            lon_deg=settings.LON_MIN + lon_idx * settings.RESOLUTION_DEG
        )

        return {
            "lead_day": lead_day,
            "coordinate": {
                "lat": round(settings.LAT_MIN + lat_idx * settings.RESOLUTION_DEG, 2),
                "lon": round(settings.LON_MIN + lon_idx * settings.RESOLUTION_DEG, 2)
            },
            "variable_attributions": channel_contributions,
            "primary_driver": ranked_vars[0][1]["name"],
            "primary_driver_pct": ranked_vars[0][1]["percentage"],
            "secondary_driver": ranked_vars[1][1]["name"],
            "secondary_driver_pct": ranked_vars[1][1]["percentage"],
            "meteorological_briefing": briefing,
            "spatial_saliency": spatial_heat_norm.tolist()
        }

    def _generate_meteorological_briefing(
        self,
        ranked_vars: List[Tuple[str, Dict]],
        lead_day: int,
        lat_deg: float,
        lon_deg: float
    ) -> str:
        """
        Synthesizes an operational meteorological diagnosis based on attribution scores.
        """
        top_var = ranked_vars[0][0]
        top_pct = ranked_vars[0][1]["percentage"]
        sec_var = ranked_vars[1][0]
        sec_pct = ranked_vars[1][1]["percentage"]
        
        driver_narratives = {
            "z500": f"Uncertainty at Day {lead_day} is dominated by 500 hPa Geopotential Height anomalies ({top_pct}% attribution). Indicates mid-latitude westerly trough phase error or subtropical ridge positioning displacement over {lat_deg:.1f}°N, {lon_deg:.1f}°E.",
            "mslp": f"Primary bust risk is governed by Mean Sea Level Pressure deficits ({top_pct}% attribution). Points to cyclonic center track divergence and underpredicted surface isobaric pressure gradient.",
            "vort850": f"Bust sensitivity is primarily driven by 850 hPa relative vorticity shear ({top_pct}% attribution). Reflects low-level cyclonic monsoon vortex shearing and steering flow uncertainty.",
            "precip": f"High error susceptibility driven by convective rainfall parameterization ({top_pct}% attribution). Indicates intense precipitation false-alarm or orographic lifting underestimation.",
            "pwat": f"Dominant bust mechanism is Precipitable Water flux divergence ({top_pct}% attribution). Represents moisture transport boundary layer errors from the Arabian Sea / Bay of Bengal."
        }

        recommendations = {
            "z500": "Operational Advice: Review upper-air jet streak isotachs and inspect ECMWF/GFS ensemble member spread on westerly trough amplitude.",
            "mslp": "Operational Advice: Check surface barometric trend stations and sea-surface temperature anomalies in the cyclogenesis region.",
            "vort850": "Operational Advice: Examine low-level wind shear vectors (850–200 hPa) and verify vortex tilt against satellite water vapor imagery.",
            "precip": "Operational Advice: Cross-reference ensemble probability of exceedance (>50mm) against Doppler weather radar and high-resolution radar assimilation.",
            "pwat": "Operational Advice: Monitor microwave sounder moisture profiles and low-level moisture convergence along the coastal boundary."
        }

        primary_text = driver_narratives.get(top_var, f"Synoptic bust driven by {top_var} ({top_pct}%).")
        secondary_text = f"Secondary contributing synoptic factor: {settings.CHANNEL_NAMES[sec_var]} ({sec_pct}%)."
        advice_text = recommendations.get(top_var, "Operational Advice: Verify against multi-model ensemble consensus.")

        return f"{primary_text} {secondary_text} {advice_text}"
