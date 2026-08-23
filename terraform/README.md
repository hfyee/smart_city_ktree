# EDM Group 01 — Terraform

Provisions the group's EC2 estate: 1 DB host (chromadb + mongodb + neo4j) and
3 small general-purpose workers, all with a nightly 01:00 UTC auto-shutdown.

## IAM role review (`EDM_AWS_ROLE_01`)

This role is created and owned by a **separate** Terraform project — this
project only assumes it and never modifies it. Reviewed permissions
(`arn:aws:iam::200810865757:role/lab-groups/EDM_AWS_ROLE_01`, region
`ap-southeast-1` only):

| Service | Allowed | Notes |
|---|---|---|
| EC2 | `Describe*` anywhere; `RunInstances` **only** into `subnet-0853cb9556de61de5`; create/manage own tagged (`GroupTag=01`) security groups & key pairs; start/stop/terminate only instances already tagged `GroupTag=01` | No VPC/subnet/IGW/NAT creation rights |
| IAM | **none** | No `CreateRole`/`PassRole` → **no instance profiles → no SSM Session Manager.** SSH key pair is the only access path. |
| CloudWatch/Events | Logs, metrics, dashboards; create/manage EventBridge rules tagged `GroupTag=01` | No `lambda:AddPermission` → an EventBridge→Lambda shutdown pattern won't work under this role |
| Lambda | Create/manage own tagged functions | Not used by this project |
| Glue | Create/manage own tagged catalog resources | Not used by this project |
| S3 | R/W only on `edm-s3-01-200810865757` | Used for Terraform remote state (`backend.tf`) — the only bucket this role can reach |
| RDS / ELB / ASG | not granted | out of scope |

**Network finding:** `subnet-0853cb9556de61de5` (VPC `vpc-07d617bf1d097edcd`)
had no Internet Gateway, no NAT Gateway, and no VPC endpoints at review
time. An **Internet Gateway has since been attached to the VPC** (done
outside this role's/project's permissions, by whoever owns the networking),
so instances now get internet egress and, with `assign_public_ip = true`,
a public IP for SSH.

**Because a role with no `RunInstances` outside one subnet also has no
`iam:PassRole`,** this project deliberately avoids anything needing an
instance profile (SSM, CloudWatch agent auto-config, etc.) — access is by
SSH key only, and shutdown is a local cron job rather than an
EventBridge/Lambda schedule (which the role also can't fully wire up).

### Capabilities this project does **not** have and does not attempt to add

If any of these turn out to be needed, request them from whoever owns
`EDM_AWS_ROLE_01` — do not add them here:

- `ec2:CreateTags` on `volume/*` — the AWS provider tags EBS volumes
  (root/data) via a follow-up `CreateTags` call whenever any tags are
  computed for them; this project works around it by never setting `tags`
  on `root_block_device`/`ebs_block_device` (see `locals.tf`), so the
  volumes end up untagged rather than requesting broader permissions.

  **Related gotcha, already tagged resources (SG/key pair/instances):**
  `aws:RequestTag/GroupTag=01` is evaluated against the tags in *that
  specific* `CreateTags` API call, not the resource's full tag set. If you
  add/remove a tag key on an SG, key pair, or instance that's already been
  created, the AWS provider sends a partial update containing only the
  changed key(s) — if that partial call doesn't happen to include
  `GroupTag`, the condition has nothing to match and the whole call is
  denied, even though `GroupTag=01` is already sitting on the resource
  unchanged. **Don't change the tag set on already-applied SG/key
  pair/instance resources** (adding, removing, or renaming keys). If new
  tags are genuinely needed, destroy and recreate the resource so the
  full tag set — `GroupTag` included — goes through in a single
  `CreateTags`/creation call instead of a partial update.
- `ec2:AllocateAddress` / `AssociateAddress` / `ReleaseAddress` — for a
  **static** Elastic IP (currently instances get a dynamic public IP that
  changes on stop/start, now that the IGW is live).
- `iam:CreateInstanceProfile` / `PassRole` — for SSM Session Manager access
  instead of SSH.
- `ec2:CreateVpc` / `CreateSubnet` / `CreateInternetGateway` — networking is
  entirely out of this role's/project's scope (IGW has already been added
  separately).

## Layout

```
terraform/
├── provider.tf, versions.tf     # AWS provider (runs as EDM_AWS_ROLE_01), required providers
├── backend.tf                   # remote state in S3 (native locking, no DynamoDB needed)
├── variables.tf                 # all tunables, see below
├── key_pair.tf                  # generates the SSH key pair (private key never written to disk)
├── security_group.tf            # SSH ingress + intra-group DB ports
├── ec2.tf                       # 1 DB host + 3 workers, AMI lookup, auto-shutdown wiring
├── outputs.tf
├── scripts/
│   ├── auto_shutdown.tpl.sh     # cron: `shutdown -h now` at 01:00 UTC on every instance
│   └── db_host_setup.tpl.sh     # Docker + mongodb/neo4j/chromadb containers, /data volume
└── terraform.tfvars.example     # local-only reference; in CI, vars come from TF_VAR_* CI/CD variables
```

Deployment is driven by `.gitlab-ci.yml` at the repo root (see below) —
running Terraform by hand is only for local plan review.

## Deploying via GitLab CI/CD (primary path)

`.gitlab-ci.yml` (repo root) runs `tf_validate` → `tf_plan` → `tf_apply`.
Authentication uses GitLab's native OIDC federation — `EDM_AWS_ROLE_01`'s
trust policy already allows `AssumeRoleWithWebIdentity` from this project's
gitlab.com OIDC provider, so **no AWS access keys are stored in CI/CD
variables**; each job exchanges its `id_token` for role credentials
directly (the pipeline maps the existing `AWS_DEPLOY_ROLE_ARN` variable to
the `AWS_ROLE_ARN` env var the AWS SDK looks for).

Uses these **existing** CI/CD variables (Settings > CI/CD > Variables) —
none of these are defined in `.gitlab-ci.yml` itself:

| Key | Value | Used for |
|---|---|---|
| `AWS_DEPLOY_ROLE_ARN` | `EDM_AWS_ROLE_01` (role name, not full ARN) | Role the OIDC exchange assumes — the pipeline expands this to `arn:aws:iam::200810865757:role/lab-groups/EDM_AWS_ROLE_01` automatically since STS requires a full ARN |
| `AWS_DEFAULT_REGION` | `ap-southeast-1` | Picked up automatically by the AWS SDK/provider |
| `TF_STATE_BUCKET` | `edm-s3-01-200810865757` | S3 bucket for remote state, passed to `terraform init -backend-config` |

`AWS_DEPLOY_ROLE_ARN` and `TF_STATE_BUCKET` are both marked **Protected**,
which means **`dev_hrj` must be a Protected branch**
(Settings > Repository > Protected branches) or these resolve empty on it —
`main` is protected by GitLab's default branch protection already.

Plus one variable **you need to add**:

| Key | Value | Notes |
|---|---|---|
| `TF_VAR_ssh_allowed_cidrs` | e.g. `["203.0.113.10/32"]` | Team's real source IP(s)/VPN CIDR, JSON list. **Required** — the variable has no default and `terraform plan` fails without it. |

Pipeline behaviour:
- `tf_validate` — `fmt -check` + `validate`, runs on every push/MR.
- `tf_plan` — runs on MRs and on `main`/`dev_hrj` pushes, uploads the plan
  as a job artifact.
- `tf_apply` — **automatic** on `main` and `dev_hrj`: applies the exact plan
  artifact from `tf_plan` (not a fresh plan) so what gets applied is what
  was reviewed. A push to either branch deploys — review the `tf_plan`
  output before/alongside, since apply runs unattended right after.
- `tf_destroy` — **manual** on `main` and `dev_hrj`, runs `terraform destroy
  -auto-approve`. Tears down every resource this project manages — EC2
  instances, security group, key pair — **including the data on their EBS
  volumes**; there is no backup/snapshot step. Trigger it either from the
  pipeline's manual job, or from **Deployments > Environments >
  edm-group01 > Stop environment** in the GitLab UI (wired via `tf_apply`'s
  `on_stop: tf_destroy`). Unlike `tf_apply`, this never runs automatically.

⚠ Both branches sharing one `edm-group01` environment/state means `dev_hrj`
and `main` deploy and destroy the **same** EC2 instances — there's no
per-branch isolation. Pushing to either branch applies against shared
infrastructure; keep that in mind before pushing to `dev_hrj` for
experimentation.

**Troubleshooting "No valid credential sources found" / STS `roleArn`
length error at `terraform init`:**
- If the error cites `roleArn` failing a "length >= 20" constraint: STS
  needs a *full* role ARN, and `AWS_DEPLOY_ROLE_ARN` is set to just the bare
  role name (`EDM_AWS_ROLE_01`, 15 chars). The pipeline's `before_script`
  now expands short names to the full ARN automatically — if this still
  fails, confirm the value hasn't changed shape (e.g. to a different role
  name or a partial ARN) in a way the `case` expansion doesn't expect.
- If `AWS_DEPLOY_ROLE_ARN` (or `TF_STATE_BUCKET`) resolved **empty**
  instead (a separate failure the same `before_script` check catches),
  two usual causes:
- The variable is marked **Protected** in Settings > CI/CD > Variables, but
  the branch the pipeline ran on isn't a **Protected branch** (Settings >
  Repository > Protected branches) — Protected variables are withheld on
  non-protected branches. This project's variables are Protected, so
  **`dev_hrj` needs to be added as a Protected branch** for the pipeline to
  work on it (`main` is protected by GitLab's default already).
- The variable has an **Environment scope** that doesn't match the job —
  only `tf_apply` currently declares `environment: edm-group01`; if the
  variable is scoped to a specific environment name, `tf_validate`/`tf_plan`
  (which have none) won't see it. (Not the case here — this project's
  variables are scoped to "All".)

### Remote state

State lives at `s3://${TF_STATE_BUCKET}/terraform/edm-group01-ec2.tfstate`
— currently `s3://edm-s3-01-200810865757/terraform/edm-group01-ec2.tfstate`
(see `backend.tf`, bucket supplied via `-backend-config` from the
`TF_STATE_BUCKET` CI/CD variable) — required because CI job containers are
stateless and a local backend would lose state between jobs/pipelines.

The bucket is the one `EDM_AWS_ROLE_01`'s S3 policy actually grants access
to — its policy covers exactly `edm-s3-01-200810865757` and nothing else,
so this project's state necessarily lives there rather than in some other
shared bucket. The key (`terraform/edm-group01-ec2.tfstate`) is scoped
under its own prefix precisely so it can't collide with anything else that
bucket might be used for.

Locking uses Terraform's native S3 conditional-write locking
(`use_lockfile`, requires Terraform ≥ 1.10) since the role has no DynamoDB
permissions for the older lock-table approach.

## Running locally (optional, e.g. for `terraform plan` review)

The role has no `sts:AssumeRole` permission on itself, so unlike CI (which
authenticates *as* the role directly via OIDC), local runs need your own
IAM user to assume the role first. Add to `~/.aws/config`:

```ini
[profile edm-group01]
role_arn       = arn:aws:iam::200810865757:role/lab-groups/EDM_AWS_ROLE_01
source_profile = default   # or whichever profile holds your IAM user creds
region         = ap-southeast-1
```

Then:

```bash
export AWS_PROFILE=edm-group01
cp terraform.tfvars.example terraform.tfvars   # set ssh_allowed_cidrs
terraform init -backend-config="bucket=edm-s3-01-200810865757"
terraform plan
```

Since state is shared remotely (`backend.tf`), local plans see the same
state CI does — but prefer letting CI `apply` so changes go through the
pipeline's plan/apply record.

## Accessing the EC2 instances

1. Retrieve the generated private key (only exists in Terraform state —
   never written to disk automatically, so it can't accidentally get
   committed):
   ```bash
   terraform output -raw private_key > edm-group01-key.pem
   chmod 400 edm-group01-key.pem      # macOS/Linux
   ```
   On Windows (PowerShell): `icacls edm-group01-key.pem /inheritance:r /grant:r "$($env:USERNAME):(R)"`
2. Get the IP(s):
   ```bash
   terraform output db_host_public_ip
   terraform output worker_public_ips
   ```
   (Public IPs are `null` until the Internet Gateway is attached; use the
   `*_private_ip` outputs plus VPN/Direct Connect access otherwise.)
3. SSH in as the Amazon Linux default user:
   ```bash
   ssh -i edm-group01-key.pem ec2-user@<ip>
   ```
4. On the DB host, the databases are reachable at:
   - MongoDB: `mongodb://<db-host-ip>:27017`
   - Neo4j: `bolt://<db-host-ip>:7687` / browser `http://<db-host-ip>:7474`,
     user `neo4j`, password from `terraform output -raw neo4j_password`
   - ChromaDB: `http://<db-host-ip>:8000`

   These ports are only open to other instances in the same security group
   (the 3 workers), **not** to the public internet — from your laptop you'd
   need to reach them via SSH port-forwarding, e.g.:
   ```bash
   ssh -i edm-group01-key.pem -L 27017:localhost:27017 -L 7474:localhost:7474 \
       -L 7687:localhost:7687 -L 8000:localhost:8000 ec2-user@<db-host-ip>
   ```

## Auto-shutdown

Every instance installs a cron job (`/etc/cron.d/auto-shutdown`) that runs
`shutdown -h now` daily at 01:00 UTC. This triggers a normal EC2 **Stop**
(the default instance-initiated-shutdown-behavior), not a terminate — data on
EBS volumes is preserved, only compute billing stops. Start instances again
each morning with:
```bash
terraform apply   # re-applies (no-op on config) and leaves stopped instances stopped
# or, to just start what's already there:
aws ec2 start-instances --instance-ids <id> --profile <your-profile>
```
(`ec2:StartInstances` is allowed on any instance tagged `GroupTag=01`.)

## Sizing

- DB host: `t3.xlarge` (4 vCPU / 16GiB RAM), 30 GB root + 100 GB dedicated
  `/data` volume (adjust via `db_host_instance_type` /
  `db_host_volume_size_gb` if the datasets are larger).
- Workers: `t3.small` × 3, 30 GB root volume each.

## Secrets / gitignore

`terraform.tfvars`, `*.tfstate`, `.terraform/`, generated `*.pem` key files,
and any local Claude Code memory (`.claude/`, `CLAUDE.local.md`) are all
excluded via the repo's root `.gitignore` — never commit these.
