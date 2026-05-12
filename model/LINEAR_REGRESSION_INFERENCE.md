# Linear Regression 추론 서버 배포 가이드

## 파일 구성

- `export_linear_regression_model.py`: `focustation_synthetic_3000.csv`로 Linear Regression 모델을 학습하고 배포용 `joblib` bundle을 저장합니다.
- `inference_linear_regression.py`: 저장된 모델을 로드해서 예측만 수행합니다.
- `outputs_linear_regression/models/linear_regression.joblib`: 서버에 올릴 모델 파일입니다. 아래 export 명령 실행 후 생성됩니다.

## 의존성 설치

```bash
pip install pandas numpy scikit-learn joblib
```

## 모델 파일 생성

현재 폴더에서 한 번 실행합니다.

```bash
python3 export_linear_regression_model.py
```

생성되는 주요 파일:

```text
outputs_linear_regression/models/linear_regression.joblib
outputs_linear_regression/metrics/linear_regression_metrics.json
```

서버에는 최소한 아래 파일을 같이 올리면 됩니다.

```text
inference_linear_regression.py
outputs_linear_regression/models/linear_regression.joblib
```

## CSV로 추론 실행

입력 CSV에는 학습 때 사용한 feature column이 모두 있어야 합니다. `satisfaction_score`, `split`, `interaction_id` 같은 컬럼은 없어도 됩니다.

```bash
python3 inference_linear_regression.py \
  --input sample_input.csv \
  --output predictions.csv
```

결과 파일에는 `predicted_satisfaction_score` 컬럼이 추가됩니다.

## JSON으로 추론 실행

단일 record 또는 record 배열을 입력할 수 있습니다.

```bash
python3 inference_linear_regression.py \
  --input sample_input.json \
  --output predictions.json
```

## 서버 코드에서 import해서 사용

```python
from inference_linear_regression import predict_satisfaction

score = predict_satisfaction({
    "user_type": "balanced",
    "pref_quiet": 4,
    "pref_light": 4,
    "pref_low_crowd": 4,
    "pref_privacy": 3,
    "pref_outlet": 5,
    "pref_distance": 4,
    "pref_thermal_air": 4,
    "pref_control": 3,
    "pref_comfort": 3,
    "pref_deepwork": 4,
    "general_place_type": "study_room",
    "general_task_type": "coding",
    "general_social_mode": "mostly_solo",
    "general_stay_duration": "under_1h",
    "general_time_slot": "afternoon",
    "general_distraction_noise": 1,
    "general_distraction_crowd": 1,
    "general_distraction_visual": 0,
    "general_distraction_temperature": 1,
    "general_distraction_outlet": 1,
    "general_distraction_distance": 1,
    "general_priority_quiet": 1,
    "general_priority_outlet": 1,
    "general_priority_distance": 1,
    "general_priority_comfort": 0,
    "general_priority_privacy": 0,
    "place_type": "home",
    "task_type": "report_writing",
    "group_size": "solo",
    "stay_duration": "2_4h",
    "time_slot": "evening",
    "day_type": "weekday",
    "distance_minutes": 17.2,
    "weather": "cloudy",
    "indoor_outdoor": "indoor",
    "visit_frequency": "sometimes",
    "place_quiet": 4,
    "place_light": 4,
    "place_low_crowd": 4,
    "place_low_visual_distraction": 4,
    "place_control": 4,
    "place_comfort": 4,
    "place_outlet": 4,
    "place_task_fit": 5,
    "place_temperature_air": 4,
    "place_seat_availability": 5,
    "quiet_match": 16,
    "light_match": 16,
    "crowd_match": 16,
    "privacy_match": 12,
    "outlet_match": 20,
    "thermal_air_match": 16,
    "control_match": 12,
    "comfort_match": 12,
    "deepwork_task_match": 3.4,
    "distance_penalty": 8.6,
    "task_place_fit_match": 20,
    "time_match": 0.5,
})
```

## 입력 feature column

```text
user_type
pref_quiet
pref_light
pref_low_crowd
pref_privacy
pref_outlet
pref_distance
pref_thermal_air
pref_control
pref_comfort
pref_deepwork
general_place_type
general_task_type
general_social_mode
general_stay_duration
general_time_slot
general_distraction_noise
general_distraction_crowd
general_distraction_visual
general_distraction_temperature
general_distraction_outlet
general_distraction_distance
general_priority_quiet
general_priority_outlet
general_priority_distance
general_priority_comfort
general_priority_privacy
place_type
task_type
group_size
stay_duration
time_slot
day_type
distance_minutes
weather
indoor_outdoor
visit_frequency
place_quiet
place_light
place_low_crowd
place_low_visual_distraction
place_control
place_comfort
place_outlet
place_task_fit
place_temperature_air
place_seat_availability
quiet_match
light_match
crowd_match
privacy_match
outlet_match
thermal_air_match
control_match
comfort_match
deepwork_task_match
distance_penalty
task_place_fit_match
time_match
```

## 주의사항

- `linear_regression.joblib`은 학습 당시 feature column 순서와 전처리기를 함께 포함합니다.
- 추론 시 누락된 feature column이 있으면 에러를 발생시킵니다.
- 기본값으로 예측값을 `0-100` 범위로 clip합니다. 원본 예측값이 필요하면 `--no-clip`을 사용합니다.
- 현재 저장된 기존 산출물에는 XGBoost/LightGBM 모델만 있었기 때문에 Linear Regression 모델은 새로 export해야 합니다.
