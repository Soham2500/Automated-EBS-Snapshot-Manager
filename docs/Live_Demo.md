# Live Demo Guide

## Safe demonstration sequence

1. Set `dry_run` to `true` and configure two non-sensitive example volume IDs.
2. Run `python snapshot_manager.py`.
3. Show the logs for simulated creation, simulated cleanup, and execution time.
4. Open `reports/snapshot_report.csv` and identify both generated rows.
5. Start `python dashboard/app.py` and show the four metric cards.
6. Run `pytest -q` to demonstrate isolated AWS unit tests.
7. With approval in a sandbox AWS account, change `dry_run` to `false`, use a real
   volume, and rerun.
8. Verify the snapshot tags in EC2, the SNS message, and Lambda CloudWatch logs.
9. Demonstrate restore with `restore_volume.py`, then delete the temporary restored
   volume after verification.

## Expected talking points

- Multi-volume failures are isolated; the run returns `partial_failure` with details.
- Cleanup is ownership-tag constrained to reduce accidental deletion risk.
- No AWS credentials are present in the project.
- EventBridge provides scheduling, while Lambda supplies serverless execution.
- The local CSV enables a simple dashboard; durable centralized reports are a
  natural production extension.

## Demo evidence checklist

- Lambda test invocation result
- CloudWatch log entry containing `execution_time_seconds`
- EC2 snapshot tags and source volume
- SNS delivery confirmation
- Dashboard overview
- Passing GitHub Actions workflow
