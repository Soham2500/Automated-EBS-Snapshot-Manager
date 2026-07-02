# Project Report

## Executive summary

The Automated AWS EBS Snapshot Manager provides scheduled, policy-based backups for
multiple EBS volumes. It runs as an AWS Lambda function invoked by EventBridge
Scheduler, creates tagged snapshots, removes expired project-owned snapshots,
publishes SNS notifications, emits CloudWatch-compatible logs, and generates a CSV
activity report for a lightweight Flask dashboard.

## Business problem

Manual snapshots are inconsistent, difficult to audit, and prone to unbounded
storage growth. This project standardizes the backup schedule and retention policy,
gives operators immediate creation notifications, and preserves restoration as a
documented, repeatable operation.

## Delivered capabilities

- JSON-driven Region, volume, retention, SNS, restore, report, and dry-run settings.
- Multi-volume processing with per-volume failure isolation.
- Tagged snapshot creation and ownership-scoped lifecycle cleanup.
- Structured operational logging suitable for Lambda CloudWatch Logs.
- CSV reporting and a read-only status dashboard.
- Snapshot-to-volume disaster recovery CLI.
- Unit tests with mocked AWS clients and automated CI checks.
- Deployment, setup, architecture, demo, and interview documentation.

## Reliability and security

The code relies on IAM roles and the Boto3 credential chain rather than embedded
secrets. Cleanup requires account ownership plus two management tags. Dry-run mode
supports safe rehearsals. Error messages are collected into the result while logs
retain diagnostic stack traces. SNS failure does not discard an already-created
snapshot or prevent subsequent volume processing.

## Operational considerations

Snapshot creation is asynchronous: a successful API response generally reports
`pending`, and EBS completes the data-plane work afterward. Organizations requiring
completion confirmation should add an EventBridge event or waiter-based follow-up.
Lambda `/tmp` reports are ephemeral, so long-term compliance history should be sent
to S3 or another durable system. CloudWatch alarms should monitor error signatures,
duration, throttling, and missing expected invocations.

## Success criteria

- Every configured volume receives a creation attempt per scheduled execution.
- Managed snapshots older than retention are selected for deletion.
- The execution result identifies created and deleted snapshot IDs and errors.
- Creation, deletion, exceptions, and total execution time appear in logs.
- CI rejects lint violations and test regressions.
