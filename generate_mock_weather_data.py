#!/usr/bin/env python3
"""
generate_mock_weather_data.py

Operational Synthetic Data Generator for Medium-Range NWP Forecast Bust Detection.
Simulates 10-day gridded forecasts and ground truth verification across South Asia
(5°N–38°N, 65°E–100°E) with realistic synoptic anomalies.

Usage:
    python generate_mock_weather_data.py --output-dir data/ --scenario western_disturbance
    python generate_mock_weather_data.py --output-dir data/ --all-scenarios
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.ml.data_generator import WeatherDataGenerator
from backend.app.core.config import settings

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic 10-day NWP forecast and verification datasets for South Asia."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Directory where output NetCDF4 files will be saved."
    )
    parser.add_argument(
        "--scenario",
        type=str,
        choices=["western_disturbance", "monsoon_depression", "monsoon_break", "climatology"],
        default="western_disturbance",
        help="Specific bust scenario to simulate."
    )
    parser.add_argument(
        "--all-scenarios",
        action="store_true",
        help="Generate NetCDF datasets for all supported operational bust scenarios."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible synoptic turbulence."
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generator = WeatherDataGenerator(seed=args.seed)
    
    scenarios_to_run = (
        ["western_disturbance", "monsoon_depression", "monsoon_break", "climatology"]
        if args.all_scenarios
        else [args.scenario]
    )
    
    print("=" * 70)
    print("AeroCast BustSentinel: Synthetic NWP Data Engine")
    print(f"Domain: {settings.LAT_MIN}°N–{settings.LAT_MAX}°N, {settings.LON_MIN}°E–{settings.LON_MAX}°E")
    print(f"Resolution: {settings.RESOLUTION_DEG}° | Lead Times: Day {settings.MIN_LEAD_DAY} to Day {settings.MAX_LEAD_DAY}")
    print(f"Variables: {', '.join(settings.CHANNELS)}")
    print("=" * 70)
    
    for sc in scenarios_to_run:
        out_file = output_dir / f"scenario_{sc}.nc"
        print(f"\n[+] Simulating Scenario: '{sc}'...")
        ds, meta = generator.simulate_scenario(sc)
        ds.to_netcdf(out_file, engine="netcdf4")
        print(f"    ✓ Successfully saved to: {out_file} ({out_file.stat().st_size / (1024*1024):.2f} MB)")
        print(f"    • Description: {meta['description']}")
        print(f"    • Primary Synoptic Driver: {meta['primary_driver']}")
        if meta["bust_regions"]:
            print(f"    • Alert Hotspots: {', '.join(meta['bust_regions'])}")

    print("\n[✓] Synthetic data generation complete.\n")

if __name__ == "__main__":
    main()
