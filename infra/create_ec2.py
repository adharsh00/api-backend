"""Launch an EC2 instance and bootstrap the full application stack via UserData."""
import boto3

ec2 = boto3.resource("ec2", region_name="eu-west-1")

# ---------------------------------------------------------------------------
# UserData bootstrap script — runs once on first boot as root
# ---------------------------------------------------------------------------
USER_DATA = """#!/bin/bash
set -e
yum update -y
yum install -y git python3 python3-pip nodejs npm nginx file-libs

# ── Clone repository ──────────────────────────────────────────────────────
cd /home/ec2-user
git clone https://github.com/adharsh00/api-backend
cd api-backend/backend

# ── Install Python dependencies ───────────────────────────────────────────
pip3 install -r requirements.txt

# ── FastAPI systemd service ───────────────────────────────────────────────
cat > /etc/systemd/system/api.service <<'EOF'
[Unit]
Description=FastAPI Image Validation Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/api-backend/backend
ExecStart=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
EnvironmentFile=/home/ec2-user/api-backend/.env

[Install]
WantedBy=multi-user.target
EOF

# ── SQS Worker systemd service ────────────────────────────────────────────
cat > /etc/systemd/system/worker.service <<'EOF'
[Unit]
Description=SQS Image Validation Worker
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/api-backend/backend
ExecStart=/usr/bin/python3 workers/image_worker.py
Restart=always
EnvironmentFile=/home/ec2-user/api-backend/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable api worker
systemctl start api worker

# ── Build Vue.js frontend ─────────────────────────────────────────────────
cd /home/ec2-user/api-backend/frontend
npm install
npm run build

# ── Configure Nginx ───────────────────────────────────────────────────────
cat > /etc/nginx/conf.d/app.conf <<'EOF'
server {
    listen 80;
    root /home/ec2-user/api-backend/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

systemctl enable nginx
systemctl start nginx
"""


def create_instance(sg_id: str) -> None:
    instances = ec2.create_instances(
        ImageId="ami-0d1b55a6d77a0c326",   # Amazon Linux 2023 (eu-west-1)
        InstanceType="t3.micro",
        MinCount=1,
        MaxCount=1,
        KeyName="cloud-key-pair",
        SecurityGroupIds=[sg_id],
        UserData=USER_DATA,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": "image-validation-api"}],
            }
        ],
    )
    instance = instances[0]
    print(f"EC2 instance created: {instance.id}")
    print("Waiting for instance to reach 'running' state…")
    instance.wait_until_running()
    instance.reload()
    print(f"Public IP:  {instance.public_ip_address}")
    print(f"Public DNS: {instance.public_dns_name}")
    return instance


if __name__ == "__main__":
    import sys
    sg = sys.argv[1] if len(sys.argv) > 1 else input("Enter Security Group ID: ")
    create_instance(sg_id=sg)
