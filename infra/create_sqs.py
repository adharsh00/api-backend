"""Create the SQS queue used for asynchronous image validation tasks."""
import boto3

sqs = boto3.client("sqs", region_name="eu-west-1")
QUEUE_NAME = "image-validation-queue"


def create_queue(queue_name: str = QUEUE_NAME) -> str:
    resp = sqs.create_queue(
        QueueName=queue_name,
        Attributes={
            "VisibilityTimeout":      "60",
            "MessageRetentionPeriod": "86400",  # 1 day
            "ReceiveMessageWaitTimeSeconds": "20",  # long-polling enabled
        },
    )
    url = resp["QueueUrl"]
    print(f"SQS queue created: {url}")
    return url


if __name__ == "__main__":
    create_queue()
