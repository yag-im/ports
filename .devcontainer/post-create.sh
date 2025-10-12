#!/usr/bin/env bash

#mkdir -p /workspaces/ports/.vscode
#cp /workspaces/ports/.devcontainer/vscode/* /workspaces/ports/.vscode

make bootstrap

/usr/bin/pulseaudio --disallow-module-loading --log-level=2 --disallow-exit --exit-idle-time=-1 --high-priority=yes --realtime=yes & disown

# aws cmd line tool for ops with S3 buckets (for cloud deployments)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
unzip /tmp/awscliv2.zip -d /tmp
sudo /tmp/aws/install
