import boto3
from datetime import datetime

ec2 = boto3.client("ec2", region_name="ap-south-1")

volume_id = "vol-0da27d539b52658d8"

response = ec2.create_snapshot(
    VolumeId=volume_id,
    Description=f"Automated snapshot created at {datetime.now()}",
    TagSpecifications=[
        {
            "ResourceType": "snapshot",
            "Tags": [
                {"Key": "Name", "Value": "Python-Auto-Snapshot"},
                {"Key": "Project", "Value": "EBS-Snapshot-Manager"},
                {"Key": "CreatedBy", "Value": "Python-Boto3"},
                {"Key": "Owner", "Value": "Soham"}
            ]
        }
    ]
)

print("Snapshot Created Successfully")
print("Snapshot ID:", response["SnapshotId"])
