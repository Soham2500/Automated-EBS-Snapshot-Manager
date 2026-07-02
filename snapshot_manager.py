import boto3
from datetime import datetime, timezone, timedelta

REGION = "ap-south-1"
VOLUME_ID = "vol-0da27d539b52658d8"
RETENTION_DAYS = 7

ec2 = boto3.client("ec2", region_name=REGION)

def create_snapshot():
    response = ec2.create_snapshot(
        VolumeId=VOLUME_ID,
        Description=f"Automated snapshot created at {datetime.now()}",
        TagSpecifications=[
            {
                "ResourceType": "snapshot",
                "Tags": [
                    {"Key": "Name", "Value": "Auto-EBS-Snapshot"},
                    {"Key": "Project", "Value": "EBS-Snapshot-Manager"},
                    {"Key": "CreatedBy", "Value": "Python-Boto3"},
                    {"Key": "Owner", "Value": "Soham"},
                    {"Key": "VolumeId", "Value": VOLUME_ID}
                ]
            }
        ]
    )

    print("Snapshot Created Successfully")
    print("Snapshot ID:", response["SnapshotId"])


def cleanup_old_snapshots():
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

    snapshots = ec2.describe_snapshots(
        OwnerIds=["self"],
        Filters=[
            {"Name": "tag:Project", "Values": ["EBS-Snapshot-Manager"]},
            {"Name": "tag:VolumeId", "Values": [VOLUME_ID]}
        ]
    )

    deleted_count = 0

    for snapshot in snapshots["Snapshots"]:
        snapshot_id = snapshot["SnapshotId"]
        start_time = snapshot["StartTime"]

        if start_time < cutoff_date:
            ec2.delete_snapshot(SnapshotId=snapshot_id)
            print("Deleted old snapshot:", snapshot_id)
            deleted_count += 1
        else:
            print("Kept snapshot:", snapshot_id)

    print(f"Cleanup completed. Deleted {deleted_count} snapshot(s).")


if __name__ == "__main__":
    create_snapshot()
    cleanup_old_snapshots()
