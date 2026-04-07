# ML-server
분석 모델을 가동하기 위한 파이썬 서버

## 1. FastAPI 서버 실행

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set API_KEY=your-secret-api-key
uvicorn app.main:app --reload
```

Docker로 실행:

```bash
docker build -t focustation-ml-server .
docker run --rm -e API_KEY=your-secret-api-key -p 8000:8000 focustation-ml-server
```

서버가 실행되면 아래 엔드포인트를 사용할 수 있습니다.

- `GET /health`
- `POST /score`

`POST /score` 호출 시 `X-API-Key` 헤더가 필요합니다.

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

예시 `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/score" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d "{\"feature1\":1.5,\"feature2\":2.0,\"feature3\":3.5}"
```

## 2. Terraform으로 ALB + EC2 배포

`terraform/terraform.tfvars` 파일을 만들고 최소한 아래 값을 채워주세요.

```hcl
key_pair_name        = "your-existing-keypair"
acm_certificate_arn = "arn:aws:acm:ap-northeast-2:123456789012:certificate/xxxx"
container_image_uri = "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/focustation-ml-server:latest"
api_key             = "your-secret-api-key"
```

배포 명령:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

적용이 끝나면 출력값으로 ECR 리포지토리 URL, EC2 공인 IP, HTTPS 앱 URL을 확인할 수 있습니다.

ECR에 이미지를 올리는 예시:

```bash
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com
docker build -t focustation-ml-server .
docker tag focustation-ml-server:latest 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/focustation-ml-server:latest
docker push 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/focustation-ml-server:latest
```

## 3. 현재 범위

- CI/CD는 아직 포함하지 않았습니다.
- 현재 Terraform은 `ALB(HTTPS) -> EC2 -> Docker 컨테이너` 구조를 기준으로 합니다.
- ACM 인증서는 미리 발급되어 있다고 가정합니다.
- API key는 Terraform 변수로 전달되며, 이후에는 SSM 또는 Secrets Manager로 옮기는 것이 더 좋습니다.
