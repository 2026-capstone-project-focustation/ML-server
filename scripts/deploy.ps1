param(
    [string]$AwsRegion = "ap-northeast-2",
    [string]$TerraformDir = "terraform",
    [string]$ImageTag = "latest",
    [string]$ProjectName = "focustation-ml-server",
    [string]$LocalImageName = "focustation-ml-server",
    [string]$RemoteUser = "ec2-user",
    [string]$SshKeyPath = "",
    [int]$AppPort = 8000,
    [string]$HealthCheckPath = "/health"
)

$ErrorActionPreference = "Stop"

if ($ProjectName -notmatch '^[A-Za-z0-9._-]+$') {
    throw "ProjectName may only contain letters, numbers, dots, underscores, and hyphens."
}

if ($HealthCheckPath -notmatch '^/[A-Za-z0-9._~!$&''()*+,;=:@/%-]*$') {
    throw "HealthCheckPath must be an absolute URL path."
}

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$TerraformPath = Resolve-Path (Join-Path $RepoRoot $TerraformDir)

Write-Host "Checking AWS account..."
aws sts get-caller-identity | Out-Host

Write-Host "Reading Terraform outputs..."
$EcrRepositoryUrl = terraform -chdir="$TerraformPath" output -raw ecr_repository_url
$Ec2PublicIp = terraform -chdir="$TerraformPath" output -raw ec2_public_ip
$RegistryHost = $EcrRepositoryUrl.Split("/")[0]
$ImageUri = "${EcrRepositoryUrl}:${ImageTag}"

if ($ImageUri -notmatch '^[A-Za-z0-9._/-]+:[A-Za-z0-9._-]+$') {
    throw "Resolved ImageUri contains unsupported characters: $ImageUri"
}

Write-Host "Logging in to ECR: $RegistryHost"
aws ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin $RegistryHost

Write-Host "Building Docker image: ${LocalImageName}:${ImageTag}"
docker build -t "${LocalImageName}:${ImageTag}" "$RepoRoot"

Write-Host "Pushing Docker image: $ImageUri"
docker tag "${LocalImageName}:${ImageTag}" "$ImageUri"
docker push "$ImageUri"

Write-Host "Deploying image on EC2: $Ec2PublicIp"
$SshArgs = @()
if ($SshKeyPath -ne "") {
    $SshArgs += @("-i", $SshKeyPath)
}

$SshArgs += "${RemoteUser}@${Ec2PublicIp}"
$RemoteCommand = "sudo /opt/$ProjectName/run-container.sh '$ImageUri' && sudo systemctl enable ${ProjectName}.service && curl -fsS http://127.0.0.1:$AppPort$HealthCheckPath"

ssh @SshArgs $RemoteCommand

Write-Host "Deployment finished."
Write-Host "Health check URL: http://$Ec2PublicIp$HealthCheckPath"
