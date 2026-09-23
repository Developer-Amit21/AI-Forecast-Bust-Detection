# Model design

The system trains two tabular models: an expected absolute-error regressor and a
calibrated bust classifier. XGBoost and LightGBM are preferred when installed;
scikit-learn gradient boosting remains an explicit fallback for constrained
environments. SHAP TreeExplainer is used where available, with a transparent
feature-perturbation fallback labelled as such.

Confidence is `100 * (0.55*(1-p_bust) + 0.25*historical_reliability +
0.15*data_quality + 0.05*calibration_quality)`, clipped to 0–100. It is distinct
from bust probability, although related to it.
