"""Create the EC2 security group for the Image Validation API."""
import boto3

ec2 = boto3.client("ec2", region_name="eu-west-1")


def create_security_group(vpc_id: str) -> str:
    resp = ec2.create_security_group(
        GroupName="medical-api-sg",
        Description="Security group for the Image Validation API (FastAPI + Nginx)",
        VpcId=vpc_id,
    )
    sg_id = resp["GroupId"]

    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            # SSH — restrict to your IP in production
            {"IpProtocol": "tcp", "FromPort": 22,   "ToPort": 22,   "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH"}]},
            # HTTP
            {"IpProtocol": "tcp", "FromPort": 80,   "ToPort": 80,   "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTP"}]},
            # HTTPS
            {"IpProtocol": "tcp", "FromPort": 443,  "ToPort": 443,  "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTPS"}]},
            # FastAPI
            {"IpProtocol": "tcp", "FromPort": 8000, "ToPort": 8000, "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "FastAPI"}]},
        ],
    )
    print(f"Security group created: {sg_id}")
    return sg_id


if __name__ == "__main__":
    import sys
    vpc = sys.argv[1] if len(sys.argv) > 1 else input("Enter VPC ID: ")
    create_security_group(vpc_id=vpc)
