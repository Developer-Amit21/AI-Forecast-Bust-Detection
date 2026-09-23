export type Variable = 'precipitation' | 'temperature_2m' | 'wind_speed'
export type Prediction = {
  region_id: string; region_name: string; variable: Variable; lead_day: number;
  latitude: number; longitude: number; expected_error: number; bust_probability: number;
  confidence_score: number; risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'SEVERE';
  forecast_initialization_time: string; model_version: string; data_mode: string; source_status: string;
}
export type Explanation = { method: string; disclaimer: string; top_factors: { feature: string; contribution: number; direction: string }[] }
