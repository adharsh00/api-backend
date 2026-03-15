"""SQS worker — polls the image-validation queue and processes each message."""
import sys
import os

# Ensure the backend/ directory is on the Python path so that `app.*` imports resolve
# correctly when the worker is launched as `python workers/image_worker.py` from
# the backend/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import logging
from dotenv import load_dotenv

# Load .env from the root of the repository (two levels up from this file)
_repo_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..")
load_dotenv(os.path.join(_repo_root, ".env"))

import boto3
from app.config import AWS_REGION, SQS_QUEUE_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

sqs = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_KEY,
)


def process_message(msg: dict) -> None:
    """Handle a single SQS message.

    Currently logs the validation result. Extend this function to:
    - Write metadata to DynamoDB / RDS
    - Generate image thumbnails
    - Send email / SNS notifications
    """
    body = json.loads(msg["Body"])
    logger.info("[Worker] Processing validation result: %s", body)


def run() -> None:
    """Main polling loop — runs indefinitely until the process is killed."""
    if not SQS_QUEUE_URL:
        logger.error("[Worker] SQS_QUEUE_URL is not configured. Exiting.")
        sys.exit(1)

    logger.info("[Worker] Starting SQS long-poll loop on: %s", SQS_QUEUE_URL)

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,  # long-polling reduces cost & empty receives
            )
            messages = response.get("Messages", [])
            for msg in messages:
                try:
                    process_message(msg)
                    sqs.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=msg["ReceiptHandle"],
                    )
                    logger.info("[Worker] Message %s deleted.", msg["MessageId"])
                except Exception as exc:
                    logger.error("[Worker] Error processing message %s: %s", msg.get("MessageId"), exc)

            if not messages:
                logger.debug("[Worker] Queue empty — waiting...")
                time.sleep(5)

        except Exception as exc:
            logger.error("[Worker] SQS poll error: %s", exc)
            time.sleep(10)


if __name__ == "__main__":
    run()
