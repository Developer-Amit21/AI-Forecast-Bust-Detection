"""
Polygon and Contour Generator for Meteorological Alert Zones.
Detects contiguous high-risk bust clusters on the gridded domain,
constructs GeoJSON polygons via Shapely, and computes geographic properties.
"""
import numpy as np
from typing import List, Dict, Any
from scipy.ndimage import label
from shapely.geometry import Polygon, MultiPoint, mapping
from shapely.ops import unary_union

from backend.app.core.config import settings
from backend.app.schemas.forecast import GeoJSONFeatureCollection, GeoJSONFeature, GeoJSONGeometry, AlertZoneProperties

def get_subdivision_name(lat: float, lon: float) -> str:
    """Approximate meteorological subdivision in South Asia."""
    if lat >= 30.0 and lon <= 78.0:
        return "Northwest Himalayas (J&K, HP, Uttarakhand)"
    elif lat >= 27.0 and lon <= 77.0:
        return "Punjab, Haryana & Delhi"
    elif lat >= 24.0 and lon <= 75.0:
        return "West Rajasthan & Desert"
    elif lat >= 24.0 and lon <= 80.0:
        return "East Rajasthan & West MP"
    elif lat >= 21.0 and lon <= 82.0:
        return "Central India & Vidarbha"
    elif lat >= 18.0 and lon <= 86.0:
        return "Odisha & North Andhra Coast"
    elif lat >= 22.0 and lon <= 89.0:
        return "Gangetic West Bengal & Head Bay"
    elif lat >= 24.0 and lon >= 89.0:
        return "Northeastern States (Assam, Meghalaya)"
    elif lat <= 18.0 and lon <= 76.0:
        return "Western Ghats & Konkan Coast"
    elif lat <= 16.0 and lon >= 77.0:
        return "South Peninsular India"
    else:
        return "Bay of Bengal / Maritime Basin"

def generate_alert_polygons(
    bust_prob_grid: np.ndarray,
    confidence_grid: np.ndarray,
    lead_day: int,
    threshold: float = 0.50
) -> GeoJSONFeatureCollection:
    """
    Finds contiguous clusters of bust probability >= threshold, creates smoothed polygon
    boundaries, and computes operational risk properties.
    """
    lats = np.arange(settings.LAT_MIN, settings.LAT_MAX + 0.1, settings.RESOLUTION_DEG)
    lons = np.arange(settings.LON_MIN, settings.LON_MAX + 0.1, settings.RESOLUTION_DEG)
    
    binary_mask = (bust_prob_grid >= threshold).astype(int)
    
    # 8-connectivity structure
    structure = np.ones((3, 3), dtype=int)
    labeled_array, num_features = label(binary_mask, structure=structure)
    
    features: List[GeoJSONFeature] = []
    
    for feat_id in range(1, num_features + 1):
        cell_coords = np.argwhere(labeled_array == feat_id)
        if len(cell_coords) < 2:  # Ignore isolated single-pixel noise
            continue
            
        cluster_lats = [lats[r] for r, c in cell_coords]
        cluster_lons = [lons[c] for r, c in cell_coords]
        
        # Grid cell box expansion (+-0.5 deg around each cell center)
        box_points = []
        for r, c in cell_coords:
            la, lo = lats[r], lons[c]
            h = settings.RESOLUTION_DEG * 0.5
            box_points.extend([
                (lo - h, la - h),
                (lo + h, la - h),
                (lo + h, la + h),
                (lo - h, la + h)
            ])
            
        try:
            poly = MultiPoint(box_points).convex_hull
            # Buffer slightly and smooth
            poly_smoothed = poly.buffer(0.15).simplify(0.08)
            if not isinstance(poly_smoothed, Polygon) or poly_smoothed.is_empty:
                continue
                
            # GeoJSON coordinates format: [[[lon, lat], ...]]
            coords_raw = mapping(poly_smoothed)["coordinates"]
            
            # Risk metrics
            cell_busts = [bust_prob_grid[r, c] for r, c in cell_coords]
            cell_confs = [confidence_grid[r, c] for r, c in cell_coords]
            max_bust = float(np.max(cell_busts))
            mean_conf = float(np.mean(cell_confs))
            center_lat = float(np.mean(cluster_lats))
            center_lon = float(np.mean(cluster_lons))
            
            # Severity classification
            if max_bust >= settings.HIGH_BUST_RISK_THRESHOLD or mean_conf <= settings.LOW_CONFIDENCE_THRESHOLD:
                severity = "CRITICAL"
            elif max_bust >= settings.WATCH_BUST_RISK_THRESHOLD:
                severity = "WARNING"
            else:
                severity = "WATCH"
                
            # Approximate area in sq km: 1 deg lat ~ 111 km, 1 deg lon ~ 111 * cos(lat)
            area_deg2 = poly_smoothed.area
            area_km2 = float(area_deg2 * 111.0 * (111.0 * np.cos(np.radians(center_lat))))
            
            subdiv = get_subdivision_name(center_lat, center_lon)
            
            properties = AlertZoneProperties(
                alert_id=f"ALERT-D{lead_day}-{feat_id:02d}",
                severity=severity,
                lead_day=lead_day,
                max_bust_prob=round(max_bust, 3),
                mean_confidence=round(mean_conf, 3),
                area_sq_km=round(area_km2, 1),
                primary_driver="Compound Synoptic Dislocation",
                subdivision=subdiv,
                center_lat=round(center_lat, 2),
                center_lon=round(center_lon, 2)
            )
            
            feature = GeoJSONFeature(
                type="Feature",
                geometry=GeoJSONGeometry(
                    type="Polygon",
                    coordinates=[[[round(p[0], 4), round(p[1], 4)] for p in coords_raw[0]]]
                ),
                properties=properties
            )
            features.append(feature)
        except Exception:
            continue
            
    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)
