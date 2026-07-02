# Viva Questions and Answers

## Why use snapshots instead of copying an entire volume?

EBS snapshots are incremental at the block level after the first snapshot. They are
managed by AWS, integrate directly with volume restoration, and avoid maintaining a
custom block-copy system.

## Are snapshots immediately complete after `CreateSnapshot` returns?

No. The API normally returns a snapshot in `pending` state. EBS finishes it
asynchronously, while changed blocks remain protected by EBS during creation.

## Why are EventBridge Scheduler and Lambda used together?

Scheduler supplies a managed recurring trigger. Lambda provides on-demand compute,
CloudWatch integration, IAM role credentials, and no server administration.

## How does cleanup avoid deleting unrelated snapshots?

It lists snapshots owned by the current account and filters for both the configured
`Project` tag and `ManagedBy=snapshot-manager` before applying the age rule.

## What does dry-run guarantee?

The application simulates snapshot creation and eligible cleanup locally. It does
not call snapshot create/delete or SNS publish APIs.

## How are credentials handled?

Boto3 uses the standard provider chain. In Lambda it receives temporary credentials
from the execution role. No keys are committed to the project.

## Why inject Boto3 clients into functions?

Dependency injection makes the AWS boundary explicit and allows unit tests to use
mocks without credentials, network calls, or chargeable resources.

## What happens when one volume fails?

The error is logged and recorded, and the manager continues with the next volume.
The final status becomes `partial_failure`.

## What is the disaster recovery process?

Choose a verified snapshot, run `restore_volume.py` for the correct Availability
Zone, attach the restored volume to an instance, mount and validate the data, and
only then redirect workloads.

## Why use SNS?

SNS decouples backup execution from notification delivery and can fan out to email,
HTTPS, SQS, Lambda, or incident-management integrations.

## What should be improved for a large enterprise?

Use S3 or a database for durable reports, KMS customer-managed keys, cross-account
or cross-Region snapshot copy, AWS Backup integration, completion-state monitoring,
dead-letter queues, idempotency controls, and centralized alarms and dashboards.

## Why is the report redirected to `/tmp` on Lambda?

The deployed function directory is read-only. `/tmp` is writable but ephemeral, so
it is useful for execution-time artifacts, not long-term audit storage.
