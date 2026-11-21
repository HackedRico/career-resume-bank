---
id: acme-data-engineer
kind: role
org: Acme Freight
title: Data Engineer
location: Portland, OR
start: 2023-06
end: present
tags: [pipelines, warehouse, cost, leadership]
---

# Acme Freight, data platform

## Facts
- The nightly shipment ETL loads 2.1 million shipment records a day. Jordan rebuilt it in Python and Airflow, and its run fell from 6 hours to 40 minutes.
- The warehouse moved from on-prem PostgreSQL to Snowflake: 180 tables and 3 TB over 10 weeks, with no reporting downtime. Jordan moved the 64 finance tables and wrote the cutover checklist. Three teammates moved the rest.
- Jordan wrote 140 dbt models in SQL, with tests. Data incidents that analysts reported fell from 12 a quarter to 3.
- Jordan built the late-delivery alert: a Kafka consumer in Python scores each scan event and posts to Slack, and about 45 dispatchers reroute from it. On-time delivery rose from 91% to 94% over the two quarters after launch, and the operations lead credits the alert for the rise.
- Jordan cut Snowflake spend 28%, about $96K a year, by clustering the 5 largest tables and suspending idle warehouses.
- Jordan built the carrier scorecard in Looker. 14 account managers use it each week.
- Jordan added CI in GitHub Actions that runs 320 dbt and pytest tests on every pull request.
- Jordan wrote the on-call runbook for a rotation of 6 engineers, and mentors 2 interns.
- The platform runs 55 Airflow pipelines. Jordan moved 30 of them off cron in the first 6 months, each with retries and a Slack alert on failure.
- Jordan wrote dbt source tests that catch schema changes in 4 carrier feeds before the nightly load and alert the on-call engineer in Slack.
- About 60 analysts and account managers query the warehouse.
- Infrastructure is Terraform on AWS: S3 for landing files, Lambda for file triggers, Docker images for Airflow tasks.

## Bullets
- [pipelines] Cut the nightly shipment ETL from 6 hours to 40 minutes by rebuilding it in Python and Airflow, loading 2.1 million shipment records a day into Snowflake for 60 warehouse users.
- [cost] Saved about $96K a year, 28% of Snowflake spend, by clustering the 5 largest tables and suspending idle warehouses.
- [pipelines] Raised on-time delivery from 91% to 94% with a Kafka consumer in Python that scores each scan event and alerts 45 dispatchers in Slack to reroute late shipments.
- [warehouse] Migrated 64 finance tables from PostgreSQL to Snowflake with no reporting downtime, part of a 180-table, 3 TB warehouse move that finished in 10 weeks.
- [warehouse] Reduced analyst-reported data incidents from 12 a quarter to 3 by writing 140 dbt models with tests.
- [pipelines] Added GitHub Actions CI that runs 320 dbt and pytest tests on every pull request.
- [pipelines] Moved 30 of the platform's 55 pipelines from cron to Airflow in 6 months, each with retries and a Slack alert on failure.
- [warehouse] Caught schema changes in 4 carrier feeds before the nightly load with dbt source tests and Slack alerts.
- [warehouse] Shipped the Looker carrier scorecard that 14 account managers use each week.
- [leadership] Wrote the on-call runbook for a rotation of 6 engineers.
- [leadership] Mentor 2 interns.

## Avoid
- `\$100K|six[- ]figure` The saving is about $96K a year, so it is never rounded up to $100K (Jordan, 2026-01-05).

## Notes
- Ask Jordan: what the late-delivery alert saved in refunds.

## Links
