#!/bin/bash
dnf update -y
dnf install -y python3 python3-pip git

mkdir -p /opt/focustation-ml-server
cat <<'EOF' > /opt/focustation-ml-server/main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="FocusTation ML Server")


class ScoreRequest(BaseModel):
    feature1: float
    feature2: float
    feature3: float


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/score")
def calculate_score(payload: ScoreRequest):
    return {
        "score": payload.feature1 + payload.feature2 + payload.feature3
    }
EOF

python3 -m pip install --upgrade pip
python3 -m pip install fastapi uvicorn[standard]

cat <<'EOF' > /etc/systemd/system/focustation-fastapi.service
[Unit]
Description=FocusTation FastAPI service
After=network.target

[Service]
WorkingDirectory=/opt/focustation-ml-server
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable focustation-fastapi.service
systemctl start focustation-fastapi.service
