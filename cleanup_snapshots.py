import boto3
from datetime import datetime, timezone, timedelta

ec2 = boto3.client("ec2", region_name="ap-south-1")

RETENTION_DAYS = 7
cutoff_date = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

snapshots = ec2.describe_snapshots(
    OwnerIds=["self"],
    Filters=[
        {
            "Name": "tag:Project",
            "Values": ["EBS-Snapshot-Manager"]
        }
    ]
)

deleted_count = 0

for snapshot in snapshots["Snapshots"]:
    snapshot_id = snapshot["SnapshotId"]
    start_time = snapshot["StartTime"]

    if start_time < cutoff_date:
        ec2.delete_snapshot(SnapshotId=snapshot_id)
        print(f"Deleted old snapshot: {snapshot_id}")
        deleted_count += 1
    else:
        print(f"Kept snapshot: {snapshot_id}")

print(f"Cleanup completed. Deleted {deleted_count} snapshot(s).")
