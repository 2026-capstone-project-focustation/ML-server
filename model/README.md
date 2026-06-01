# Model

모델 관련 학습 코드, 추론 코드, 샘플 입력, 학습 데이터, 산출물은 모델 버전별 폴더에 둡니다.

```text
model/
├── linear_regression_v1/
│   ├── export_linear_regression_model.py
│   ├── inference_linear_regression.py
│   ├── focustation_synthetic_3000.csv
│   ├── sample_input.json
│   └── outputs_linear_regression/
└── sensor_target_v2/
    ├── train_sensor_target_v2.py
    ├── inference_sensor_target_v2.py
    ├── focustation_synthetic_3000_sensor_target_v2.csv
    ├── sample_input_sensor_v2_recommended.json
    └── outputs_sensor_target_v2/
```

현재 FastAPI 서버의 `/score` endpoint는 `sensor_target_v2` 모델을 로드합니다.

자세한 실행 방법:

- [linear_regression_v1](./linear_regression_v1/LINEAR_REGRESSION_INFERENCE.md)
- [sensor_target_v2](./sensor_target_v2/SENSOR_TARGET_V2_DEPLOYMENT.md)
