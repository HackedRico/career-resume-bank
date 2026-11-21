---
id: parcel-software-engineer
kind: role
org: Example Parcel Service
title: Software Engineer
location: Remote
start: 2022-07
end: 2023-05
tags: [backend, reliability]
---

# Example Parcel Service, tracking team

## Facts
- Jordan built the tracking REST API in Python with FastAPI and PostgreSQL. It serves 3 partner retailers, about 400,000 requests a day, at a p95 latency of 120 ms.
- Jordan replaced the cron job that printed shipping labels with an SQS queue and a worker. Failed labels fell from 2% to 0.1%.
- Jordan wrote integration tests in pytest that raised coverage of the tracking service from 45% to 82%.
- Jordan cut the Docker image build from 14 minutes to 4 with a multi-stage build and layer caching.
- Services run on AWS ECS, deployed with Terraform.
- Jordan added structured logging and CloudWatch dashboards to all 6 tracking services running on AWS ECS. The time to find a failed delivery event fell from 50 minutes to 8.
- Jordan wrote the partner onboarding guide and a sandbox API key flow. A new retailer now integrates in 2 days, down from 2 weeks.

## Bullets
- [backend] Built the tracking REST API in Python, FastAPI and PostgreSQL that serves 3 partner retailers 400,000 requests a day at a p95 latency of 120 ms, deployed to AWS ECS with Terraform.
- [reliability] Dropped failed shipping labels from 2% to 0.1% by replacing a cron job with an SQS queue and worker.
- [reliability] Raised test coverage of the tracking service from 45% to 82% with pytest integration tests.
- [backend] Shortened the Docker image build from 14 minutes to 4 with a multi-stage build and layer caching.
- [reliability] Trimmed the search for a failed delivery event from 50 minutes to 8 by adding structured logging and CloudWatch dashboards to all 6 tracking services running on AWS ECS.
- [backend] Shortened a new retailer's integration from 2 weeks to 2 days with an onboarding guide and a sandbox API key flow.

## Links
