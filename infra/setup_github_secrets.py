"""
infra/setup_github_secrets.py
──────────────────────────────
Reads infra/output.json (produced by setup_all.py) and sets all required
GitHub Actions repository secrets via the GitHub REST API.

Secrets set
-----------
  EC2_HOST              – EC2 public IP address
  EC2_SSH_KEY           – Contents of cloud-key-pair.pem
  AWS_ACCESS_KEY_ID     – IAM access key
  AWS_SECRET_ACCESS_KEY – IAM secret key
  S3_BUCKET_NAME        – S3 bucket name
  SQS_QUEUE_URL         – SQS queue URL

Authentication
--------------
Provide your GitHub Personal Access Token (PAT) via the
GITHUB_TOKEN environment variable or as the first CLI argument.

  python infra/setup_github_secrets.py <PAT>

The PAT must have the  `repo`  scope (or at minimum `secrets:write`).
"""

import sys
import os
import json
import base64

import boto3
import boto3.session
import requests
from nacl import encoding, public as nacl_public   # pynacl

# ── Paths ─────────────────────────────────────────────────────────────────────
_REPO_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(_REPO_ROOT, "infra", "output.json")
PEM_FILE    = os.path.join(_REPO_ROOT, "cloud-key-pair.pem")

# ── GitHub ────────────────────────────────────────────────────────────────────
GITHUB_OWNER = "adharsh00"
GITHUB_REPO  = "api-backend"
GITHUB_API   = "https://api.github.com"

# ── Resolve AWS credentials from the environment / ~/.aws/credentials ─────────
_session = boto3.session.Session()
_creds   = _session.get_credentials().get_frozen_credentials()
AWS_ACCESS_KEY_ID_VALUE     = _creds.access_key
AWS_SECRET_ACCESS_KEY_VALUE = _creds.secret_key


def _encrypt_secret(public_key_str: str, secret_value: str) -> str:
    """Encrypt *secret_value* with the repository's libsodium public key."""
    key       = nacl_public.PublicKey(public_key_str.encode("utf-8"), encoding.Base64Encoder())
    box       = nacl_public.SealedBox(key)
    encrypted = box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def _get_repo_public_key(session: requests.Session) -> tuple[str, str]:
    """Return (key_id, public_key_base64) for the repository."""
    url  = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/secrets/public-key"
    resp = session.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data["key_id"], data["key"]


def _put_secret(session: requests.Session, key_id: str, pub_key: str,
                secret_name: str, secret_value: str) -> None:
    encrypted = _encrypt_secret(pub_key, secret_value)
    url  = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/secrets/{secret_name}"
    resp = session.put(url, json={"encrypted_value": encrypted, "key_id": key_id})
    if resp.status_code in (201, 204):
        print(f"  ✅  {secret_name}")
    else:
        print(f"  ❌  {secret_name}  →  {resp.status_code} {resp.text}")


def main() -> None:
    # ── Resolve GitHub token ─────────────────────────────────────────────────
    token = (
        sys.argv[1] if len(sys.argv) > 1
        else os.environ.get("GITHUB_TOKEN", "")
    )
    if not token:
        print("ERROR: No GitHub token supplied.\n"
              "Usage:  python infra/setup_github_secrets.py <PAT>\n"
              "   or:  set GITHUB_TOKEN=<PAT> && python infra/setup_github_secrets.py")
        sys.exit(1)

    # ── Load infra output ────────────────────────────────────────────────────
    if not os.path.exists(OUTPUT_FILE):
        print(f"ERROR: {OUTPUT_FILE} not found. Run setup_all.py first.")
        sys.exit(1)

    with open(OUTPUT_FILE) as f:
        infra = json.load(f)

    ec2_ip  = infra.get("ec2_public_ip")
    sqs_url = infra.get("sqs_queue_url")
    s3_name = infra.get("s3_bucket")
    aws_key = infra.get("aws_access_key_id")

    # ── Read SSH PEM key ─────────────────────────────────────────────────────
    if not os.path.exists(PEM_FILE):
        print(f"WARNING: PEM file not found at {PEM_FILE}. EC2_SSH_KEY will be empty.")
        pem_content = ""
    else:
        with open(PEM_FILE, "r") as f:
            pem_content = f.read()

    # ── Build secrets dict ───────────────────────────────────────────────────
    secrets = {
        "EC2_HOST":              ec2_ip       or "",
        "EC2_SSH_KEY":           pem_content,
        "AWS_ACCESS_KEY_ID":     aws_key      or AWS_ACCESS_KEY_ID_VALUE,
        "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY_VALUE,
        "S3_BUCKET_NAME":        s3_name      or "medical-image-validation",
        "SQS_QUEUE_URL":         sqs_url      or "",
    }

    # ── GitHub API session ───────────────────────────────────────────────────
    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {token}",
        "Accept":        "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })

    print(f"\nSetting GitHub Actions secrets for {GITHUB_OWNER}/{GITHUB_REPO}…\n")

    key_id, pub_key = _get_repo_public_key(session)

    for name, value in secrets.items():
        _put_secret(session, key_id, pub_key, name, value)

    print("\n✅  All secrets configured. GitHub Actions CI/CD is ready.")


if __name__ == "__main__":
    main()
