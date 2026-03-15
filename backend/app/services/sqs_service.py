import boto3
import json
from app.config import AWS_REGION, SQS_QUEUE_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_KEY

sqs = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_KEY,
)


def enqueue(payload: dict) -> str:
    """Send *payload* as a JSON message to the SQS validation queue.

    Returns the SQS Message ID on success.
    """
    response = sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(payload),
    )
    return response["MessageId"]
