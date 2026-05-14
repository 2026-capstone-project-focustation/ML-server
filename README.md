# ML-server
분석 모델을 가동하기 위한 파이썬 서버

## 1. FastAPI 서버 실행

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:API_KEY="your-secret-api-key"
uvicorn app.main:app --reload
```

Linux/macOS 예시:

```bash
python -m venv .venv
source .venv/bin/activate
export API_KEY=your-secret-api-key
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

예시 응답:

```json
{
  "score": 83.42
}
```

`/score` 요청 body는 실제 Linear Regression 모델의 feature column 전체를 포함해야 합니다.
샘플 payload와 입력 컬럼 목록은 [LINEAR_REGRESSION_INFERENCE.md](./model/LINEAR_REGRESSION_INFERENCE.md)를 참고하세요.

예시 `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/score" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d @sample_input.json
```

## 2. Terraform으로 EC2 준비

`terraform/terraform.tfvars` 파일을 만들고 최소한 아래 값을 채워주세요.

```hcl
key_pair_name     = "your-existing-keypair"
api_key           = "your-secret-api-key"
allowed_ssh_cidrs = ["your-ip/32"]
```

이번 브랜치에서는 먼저 EC2와 ECR을 준비하고, 앱 이미지는 수동 스크립트로 올립니다.
따라서 `container_image_uri`는 비워두거나 생략해도 됩니다.

인프라 생성 전 AWS 계정을 확인하세요.

```bash
aws sts get-caller-identity
```

EC2와 ECR 생성:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

적용이 끝나면 출력값으로 ECR 리포지토리 URL과 EC2 공인 IP를 확인할 수 있습니다.

## 3. 수동 앱 배포

Terraform apply 후 아래 스크립트로 Docker 이미지를 빌드하고 ECR에 push한 뒤 EC2에서 실행합니다.

```powershell
.\scripts\deploy.ps1 -SshKeyPath "C:\path\to\your-key.pem"
```

배포 후 아래 주소로 health check를 확인합니다.

```bash
curl http://<ec2-public-ip>/health
```

## 4. 현재 범위

- CI/CD는 아직 포함하지 않았습니다.
- HTTPS는 아직 포함하지 않았습니다.
- 현재 Terraform은 `EC2 + Nginx + Docker 컨테이너` 구조를 기준으로 합니다.
- API key는 Terraform 변수로 전달되며, 이후에는 SSM 또는 Secrets Manager로 옮기는 것이 좋습니다.

## 5. Linear Regression 추론

Linear Regression 모델 export와 추론 실행 방법은 [LINEAR_REGRESSION_INFERENCE.md](./model/LINEAR_REGRESSION_INFERENCE.md)를 참고하세요.
