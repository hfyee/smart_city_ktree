#!/bin/bash
# Installs a daily cron job that stops the instance (EC2 default
# instance-initiated-shutdown-behavior is "stop", not "terminate") at
# ${shutdown_hour}:00 UTC to avoid overnight cost overrun.
#
# This is a local OS cron -> `shutdown -h now`, NOT an EventBridge rule.
# EDM_AWS_ROLE_01 has no lambda:AddPermission, so an EventBridge -> Lambda
# shutdown pattern is not viable under this role; the OS-level cron needs
# no AWS API permissions at all and works identically.

cat >/etc/cron.d/auto-shutdown <<'CRON'
0 ${shutdown_hour} * * * root /sbin/shutdown -h now
CRON
chmod 644 /etc/cron.d/auto-shutdown
