# ML-server
분석 모델을 가동하기 위한 파이썬 서버

## 1. FastAPI 서버 실행

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

서버가 실행되면 아래 엔드포인트를 사용할 수 있습니다.

- `GET /health`
- `POST /score`

예시 요청:

```json
{
  "feature1": 1.5,
  "feature2": 2.0,
  "feature3": 3.5
}
```

예시 응답:

```json
{
  "score": 7.0
}
```

## 2. Terraform으로 EC2 배포

`terraform/terraform.tfvars` 파일을 만들고 최소한 아래 값을 채워주세요.

```hcl
key_pair_name = "your-existing-keypair"
```

배포 명령:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

적용이 끝나면 출력값으로 EC2 공인 IP와 앱 URL을 확인할 수 있습니다.

## 3. 현재 범위

- CI/CD는 아직 포함하지 않았습니다.
- EC2 부팅 시 `user_data`로 FastAPI 앱을 바로 띄우는 기본 구조입니다.
- 이후에는 `Nginx`, `HTTPS`, `GitHub Actions`를 추가해 운영 형태로 확장하면 좋습니다.
