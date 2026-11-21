# Northwind Logistics, Data Engineer

- Source: written for this example. Northwind Logistics is not a real employer.
- Saved: 2026-01-12
- Generator: v1
- Apply: none, the post is made up
- Referral: none (Jordan, 2026-01-12)
- Status: drafted

## Post

Data Engineer, Northwind Logistics. Remote, United States.

About the role

Our data platform team moves shipment, carrier and billing data from forty source systems into one warehouse that the whole company plans from. You will build and run the data pipelines behind it.

What you will do

- Build and maintain ETL and data pipelines in Python and SQL.
- Own data quality for the tables you ship: tests, alerts and fixes.
- Work with analysts and operations teams to model new data.
- Join the on-call rotation for the platform, one week in six.

Required qualifications

- Bachelor's degree in Computer Science or a related field.
- 3+ years of experience building data pipelines in production.
- Strong Python and SQL.
- Experience with Airflow or a similar orchestrator.
- Experience with a cloud data warehouse such as Snowflake or BigQuery.
- Experience with dbt.

Preferred qualifications

- Experience with Kafka or another streaming platform.
- Infrastructure as code with Terraform.
- Experience with Spark.
- A record of cost optimization in a cloud warehouse.
- Background in logistics or supply chain data.

## Fit

- Entries used: acme-data-engineer for every required term, parcel-software-engineer for Terraform and Python services, parcel-intern and esu-teaching-assistant to keep the timeline whole, trailhead and packmule for open-source work.
- Keywords: 14/14 from the build
- Requirements: 10 met, 2 unclear, 0 not met, from the rehearsal
- Experience: 56 months of dated roles on the day the post was saved, 32 of them in the Data Engineer role

## Requirements

- Bachelor's degree in Computer Science or a related field: met, "Bachelor of Science in Computer Science | GPA: 3.8"
- 3+ years of experience building data pipelines in production: unclear, the Data Engineer role starts Jun 2023, 2 years 7 months before the post's date
- Strong Python: met, "Cut the nightly shipment ETL from 6 hours to 40 minutes by rebuilding it in Python and Airflow"
- Strong SQL: met, "writing 140 dbt models in SQL with tests"
- Experience with Airflow or a similar orchestrator: met, "Moved 30 of the platform's 55 data pipelines from cron to Airflow in 6 months"
- Experience with a cloud data warehouse such as Snowflake or BigQuery: met, "Migrated 64 finance tables from PostgreSQL to Snowflake with no reporting downtime"
- Experience with dbt: met, "writing 140 dbt models in SQL with tests"
- Experience with Kafka or another streaming platform: met, "a Kafka consumer in Python that scores each scan event"
- Infrastructure as code with Terraform: met, "deployed to AWS ECS with Terraform"
- Experience with Spark: unclear, named in the Data Engineering row and in no bullet
- A record of cost optimization in a cloud warehouse: met, "Saved about $96K a year through cost optimization, 28% of Snowflake spend"
- Background in logistics or supply chain data: met, "loading 2.1 million shipment records a day into Snowflake"

## Gaps

- Spark: `bank/skills.md` holds it only under Listed, so it prints in a Skills row and in no bullet.
- BigQuery: nothing in the bank. The post accepts Snowflake in its place.
- 3+ years of data pipelines: the bank dates pipeline work from Jun 2023. The two earlier roles built an API, a queue worker and scripts.
- Streaming beyond one Kafka consumer: the bank logs a single consumer and no streaming platform work.

## Form questions

- none shared

## Build notes

- none

## Open questions

- What did the late-delivery alert save in refunds? A dollar figure would strengthen the Kafka bullet.
- How many events a day does the Kafka consumer read? The rehearsal found the bullet thin on the stream's size.
- What does Terraform manage at Acme Freight? The only Terraform bullet sits in a role that ended in May 2023.
- Was any SQL written outside dbt, such as a tuned query or a report? One bullet carries all of the SQL evidence.
