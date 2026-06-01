# FocuStation Sensor Target v2 Deployment

## Files to upload to the ML server

Required:

```text
inference_sensor_target_v2.py
outputs_sensor_target_v2/models/ridge_sensor_target_v2.joblib
```

Recommended for record keeping / retraining:

```text
train_sensor_target_v2.py
focustation_synthetic_3000_sensor_target_v2.csv
outputs_sensor_target_v2/metrics/sensor_target_v2_metrics.json
```

Optional:

```text
focustation_synthetic_3000_sensor_target_v2.xlsx
build_sensor_target_v2.py
```

## Python dependencies

```bash
pip install pandas numpy scikit-learn joblib
```

## Android should send

Android should send existing non-derived base inputs plus these sensor primitive summaries:

```text
noise_mean_db
noise_std_db
noise_max_db
noise_p90_db
noise_spike_count
light_mean_lux
light_std_lux
light_min_lux
light_max_lux
vibration_mean
vibration_std
vibration_max
vibration_p95
vibration_spike_count
measurement_duration_sec
```

Optional but useful:

```text
valid_sample_ratio
phone_movement_ratio
```

The ML server can derive:

```text
quiet_ratio
light_range_lux
too_dark_ratio
too_bright_ratio
stillness_ratio
sample_count
sensor_quality_score
noise_level_norm
light_deviation_norm
vibration_level_norm
pref_quiet_x_noise
pref_quiet_x_noise_p90
pref_light_x_light_deviation
pref_comfort_x_vibration
pref_comfort_x_vibration_spike
```

The ML server can also derive old match features if Android sends the underlying preference/place values:

```text
quiet_match
light_match
crowd_match
privacy_match
outlet_match
thermal_air_match
control_match
comfort_match
distance_penalty
deepwork_task_match
task_place_fit_match
time_match
```

## CLI test

```bash
python3 inference_sensor_target_v2.py \
  --input sample_input.json \
  --output predictions.json
```
