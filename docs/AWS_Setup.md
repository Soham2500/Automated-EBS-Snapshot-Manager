# AWS Setup

## Prerequisites

- An AWS account and a deployment identity allowed to create IAM roles and Lambda
  functions.
- Existing EBS volume IDs in the configured Region.
- An SNS topic and confirmed subscription if notifications are required.
- Python 3.12 for a runtime matching the CI configuration.

Do not store access keys in this repository. For local development, use AWS IAM
Identity Center, an AWS profile, or environment credentials supplied by an approved
secrets system.

## IAM execution role

Create a Lambda execution role trusted by `lambda.amazonaws.com`. Attach
`AWSLambdaBasicExecutionRole` for CloudWatch logging and add a least-privilege
policy similar to this one. Replace the account, Region, volume, snapshot, and SNS
resources for the target environment.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DescribeEbsResources",
      "Effect": "Allow",
      "Action": ["ec2:DescribeSnapshots", "ec2:DescribeVolumes"],
      "Resource": "*"
    },
    {
      "Sid": "CreateAndDeleteSnapshots",
      "Effect": "Allow",
      "Action": ["ec2:CreateSnapshot", "ec2:DeleteSnapshot", "ec2:CreateTags"],
      "Resource": [
        "arn:aws:ec2:ap-south-1:123456789012:volume/*",
        "arn:aws:ec2:ap-south-1::snapshot/*"
      ]
    },
    {
      "Sid": "NotifyOperations",
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:ap-south-1:123456789012:ebs-snapshot-alerts"
    }
  ]
}
```

The restore CLI additionally needs `ec2:CreateVolume` and `ec2:CreateTags`. Give
those permissions to the operator role, not necessarily the scheduled Lambda role.

## SNS

1. Create a Standard SNS topic.
2. Add an email, HTTPS, SQS, or incident-management subscription.
3. Confirm the subscription.
4. Put the topic ARN in `config.json` as `sns_topic_arn`.

An empty ARN intentionally disables notification publishing.

## Lambda

1. Install runtime dependencies into a clean package directory.
2. Copy the top-level Python files and `config.json` into it.
3. Zip the *contents* of that directory, not the directory itself.
4. Create a Python 3.12 Lambda function using the execution role.
5. Set the handler to `snapshot_manager.lambda_handler`.
6. Use at least a 60-second timeout; increase it for large volume sets.
7. Set reserved concurrency to 1 if overlapping backup runs are undesirable.

Example packaging commands for a POSIX shell:

```bash
mkdir package
pip install -r requirements.txt -t package
cp *.py config.json package/
cd package && zip -r ../lambda-package.zip .
```

## EventBridge Scheduler

1. Create a schedule, such as `cron(0 1 * * ? *)` for 01:00 UTC daily.
2. Select the Lambda function as the target.
3. Let Scheduler create or use an execution role with `lambda:InvokeFunction`.
4. Configure retry and dead-letter queue policies appropriate to the workload.
5. Invoke once manually and inspect the CloudWatch log stream.

## CloudWatch Logs

Lambda automatically sends standard Python logging to the function log group when
its execution role has basic logging permissions. Create metric filters or alarms
for `ERROR`, `partial_failure`, and unusually high `execution_time_seconds` values.
