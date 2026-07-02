# Installation

## Local setup

```bash
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Update `config.json` with the AWS Region, source volume IDs, retention, project
name, and optional SNS topic ARN. Start with `"dry_run": true` to validate the
workflow without changing AWS resources.

## Run the manager

```bash
python snapshot_manager.py
```

The AWS SDK uses its standard credential provider chain. No credentials belong in
source files or `config.json`.

## Run the dashboard

```bash
python dashboard/app.py
```

Open `http://127.0.0.1:5000`. The dashboard reads
`reports/snapshot_report.csv`; override that path with the
`SNAPSHOT_REPORT_PATH` environment variable.

## Restore a volume

```bash
python restore_volume.py snap-0123456789abcdef0
```

The new volume is created in `availability_zone` with `volume_type` from the
configuration. Verify the target Availability Zone before restoring because an EBS
volume can only attach to an EC2 instance in the same Availability Zone.

## Quality checks

```bash
flake8 . --exclude=.git,.venv,venv,work,outputs
pytest -q
```
