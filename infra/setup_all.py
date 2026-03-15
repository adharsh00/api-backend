"""
infra/setup_all.py
──────────────────
Creates all AWS resources in the correct order and writes the results to
infra/output.json so subsequent scripts (e.g. setup_github_secrets.py) can
read them without needing to query AWS again.

Steps
-----
1.  Detect the default VPC
2.  Create the private S3 bucket (idempotent)
3.  Create the SQS queue (idempotent)
4.  Create the EC2 security group (idempotent)
5.  Launch the EC2 instance with a UserData script that
      - clones the GitHub repo
      - creates the .env file on-disk from embedded values
      - installs Python deps
      - registers & starts the FastAPI service and the SQS worker
      - builds the Vue.js frontend
      - configures and starts Nginx
6.  Wait for the EC2 to be running and print / save the public IP

Usage
-----
  python infra/setup_all.py
"""

import sys
import os
import time
import json
import textwrap

import boto3
from botocore.exceptions import ClientError

# ── Config ────────────────────────────────────────────────────────────────────
REGION        = "eu-west-1"
ACCOUNT_ID    = "843302972668"
S3_BUCKET     = "medical-image-validation"
SQS_QUEUE     = "image-validation-queue"
SG_NAME       = "medical-api-sg"
AMI_ID        = "ami-0d1b55a6d77a0c326"   # Amazon Linux 2023 (eu-west-1)
INSTANCE_TYPE = "t3.micro"
KEY_PAIR_NAME = "cloud-key-pair"
GITHUB_REPO   = "https://github.com/adharsh00/api-backend"

# Classmate API
CLASSMATE_API_KEY = "healthcare-api-key-2024"

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output.json")

# ── AWS clients ───────────────────────────────────────────────────────────────
ec2  = boto3.client("ec2",  region_name=REGION)
ec2r = boto3.resource("ec2", region_name=REGION)
s3   = boto3.client("s3",   region_name=REGION)
sqs  = boto3.client("sqs",  region_name=REGION)

# ── Read AWS creds from environment / ~/.aws/credentials ─────────────────────
import boto3.session
_session      = boto3.session.Session()
_raw_creds    = _session.get_credentials()
_creds        = _raw_creds.get_frozen_credentials()
AWS_KEY       = _creds.access_key
AWS_SEC       = _creds.secret_key


# ─────────────────────────────────────────────────────────────────────────────
def step(msg: str) -> None:
    print(f"\n{'─'*60}\n  {msg}\n{'─'*60}")


# ─────────────────────────────────────────────────────────────────────────────
def get_default_vpc() -> str:
    step("Detecting default VPC")
    resp = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])
    vpc_id = resp["Vpcs"][0]["VpcId"]
    print(f"Default VPC: {vpc_id}")
    return vpc_id


# ─────────────────────────────────────────────────────────────────────────────
def create_s3_bucket() -> str:
    step(f"Creating S3 bucket: {S3_BUCKET}")
    try:
        s3.create_bucket(
            Bucket=S3_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        print(f"Bucket created: {S3_BUCKET}")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            print(f"Bucket already exists: {S3_BUCKET}")
        else:
            raise

    # Block all public access
    s3.put_public_access_block(
        Bucket=S3_BUCKET,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls":       True,
            "IgnorePublicAcls":      True,
            "BlockPublicPolicy":     True,
            "RestrictPublicBuckets": True,
        },
    )
    # Server-side encryption
    s3.put_bucket_encryption(
        Bucket=S3_BUCKET,
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )
    return S3_BUCKET


# ─────────────────────────────────────────────────────────────────────────────
def create_sqs_queue() -> str:
    step(f"Creating SQS queue: {SQS_QUEUE}")
    try:
        resp = sqs.create_queue(
            QueueName=SQS_QUEUE,
            Attributes={
                "VisibilityTimeout":             "60",
                "MessageRetentionPeriod":        "86400",
                "ReceiveMessageWaitTimeSeconds": "20",
            },
        )
        url = resp["QueueUrl"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "QueueAlreadyExists":
            resp = sqs.get_queue_url(QueueName=SQS_QUEUE)
            url  = resp["QueueUrl"]
            print(f"Queue already exists: {url}")
        else:
            raise
    print(f"SQS queue URL: {url}")
    return url


# ─────────────────────────────────────────────────────────────────────────────
def create_security_group(vpc_id: str) -> str:
    step(f"Creating security group: {SG_NAME}")

    # Check if it already exists
    try:
        resp   = ec2.describe_security_groups(
            Filters=[{"Name": "group-name", "Values": [SG_NAME]}]
        )
        groups = resp["SecurityGroups"]
        if groups:
            sg_id = groups[0]["GroupId"]
            print(f"Security group already exists: {sg_id}")
            return sg_id
    except ClientError:
        pass

    resp  = ec2.create_security_group(
        GroupName=SG_NAME,
        Description="Security group for the Image Validation API (FastAPI + Nginx)",
        VpcId=vpc_id,
    )
    sg_id = resp["GroupId"]

    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 22,   "ToPort": 22,   "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            {"IpProtocol": "tcp", "FromPort": 80,   "ToPort": 80,   "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            {"IpProtocol": "tcp", "FromPort": 443,  "ToPort": 443,  "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            {"IpProtocol": "tcp", "FromPort": 8000, "ToPort": 8000, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
        ],
    )
    print(f"Security group created: {sg_id}")
    return sg_id


# ─────────────────────────────────────────────────────────────────────────────
def build_user_data(sqs_url: str) -> str:
    """Return the EC2 UserData bootstrap script with .env values embedded."""
    env_content = textwrap.dedent(f"""\
        AWS_REGION={REGION}
        AWS_ACCESS_KEY_ID={AWS_KEY}
        AWS_SECRET_ACCESS_KEY={AWS_SEC}
        S3_BUCKET_NAME={S3_BUCKET}
        SQS_QUEUE_URL={sqs_url}
        CLASSMATE_API_KEY={CLASSMATE_API_KEY}
    """)

    script = f"""#!/bin/bash
set -e
exec > /var/log/user-data.log 2>&1

echo "=== Starting bootstrap ==="

# System packages
yum update -y
yum install -y git python3 python3-pip nodejs npm nginx file-libs

# Upgrade pip
pip3 install --upgrade pip

# Clone the repository
cd /home/ec2-user
git clone {GITHUB_REPO}
cd api-backend

# Create .env file BEFORE starting services
cat > /home/ec2-user/api-backend/.env <<'ENVEOF'
{env_content}
ENVEOF
chown ec2-user:ec2-user /home/ec2-user/api-backend/.env
chmod 600 /home/ec2-user/api-backend/.env

# Install Python backend dependencies
cd /home/ec2-user/api-backend/backend
pip3 install -r requirements.txt

# ── FastAPI systemd service ──────────────────────────────────────────────────
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

# ── SQS Worker systemd service ───────────────────────────────────────────────
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

# ── Vue.js frontend build ────────────────────────────────────────────────────
cd /home/ec2-user/api-backend/frontend
npm install
npm run build

# ── Nginx configuration ──────────────────────────────────────────────────────
cat > /etc/nginx/conf.d/app.conf <<'EOF'
server {{
    listen 80;
    root /home/ec2-user/api-backend/frontend/dist;
    index index.html;

    location / {{
        try_files $uri $uri/ /index.html;
    }}

    location /api/ {{
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}
EOF

systemctl enable nginx
systemctl start nginx

echo "=== Bootstrap complete ==="
"""
    return script


# ─────────────────────────────────────────────────────────────────────────────
def launch_ec2(sg_id: str, sqs_url: str) -> dict:
    step("Launching EC2 instance")

    # Check if an instance with our tag is already running
    resp = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name",           "Values": ["image-validation-api"]},
            {"Name": "instance-state-name","Values": ["pending", "running"]},
        ]
    )
    reservations = resp["Reservations"]
    if reservations:
        inst = reservations[0]["Instances"][0]
        print(f"EC2 instance already running: {inst['InstanceId']}")
        return inst

    user_data = build_user_data(sqs_url)

    instances = ec2r.create_instances(
        ImageId=AMI_ID,
        InstanceType=INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        KeyName=KEY_PAIR_NAME,
        SecurityGroupIds=[sg_id],
        UserData=user_data,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": "image-validation-api"}],
        }],
    )
    instance = instances[0]
    print(f"EC2 instance created: {instance.id}")
    print("Waiting for instance to be running (this may take ~60 s)…")
    instance.wait_until_running()
    instance.reload()
    print(f"Instance running!  Public IP: {instance.public_ip_address}")
    return {"InstanceId": instance.id, "PublicIpAddress": instance.public_ip_address}


# ─────────────────────────────────────────────────────────────────────────────
def save_output(data: dict) -> None:
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nOutput saved to {OUTPUT_FILE}")


# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    vpc_id   = get_default_vpc()
    s3_name  = create_s3_bucket()
    sqs_url  = create_sqs_queue()
    sg_id    = create_security_group(vpc_id)
    ec2_info = launch_ec2(sg_id, sqs_url)

    output = {
        "region":          REGION,
        "vpc_id":          vpc_id,
        "s3_bucket":       s3_name,
        "sqs_queue_url":   sqs_url,
        "security_group":  sg_id,
        "ec2_instance_id": ec2_info.get("InstanceId"),
        "ec2_public_ip":   ec2_info.get("PublicIpAddress"),
        "aws_access_key_id": AWS_KEY,
    }
    save_output(output)

    print("\n" + "="*60)
    print(" INFRASTRUCTURE SETUP COMPLETE")
    print("="*60)
    print(f"  S3 Bucket:    {s3_name}")
    print(f"  SQS URL:      {sqs_url}")
    print(f"  Security GRP: {sg_id}")
    print(f"  EC2 ID:       {output['ec2_instance_id']}")
    print(f"  EC2 IP:       {output['ec2_public_ip']}")
    print("\nNext step: run  python infra/setup_github_secrets.py")


if __name__ == "__main__":
    main()
