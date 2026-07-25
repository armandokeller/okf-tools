---
type: Attested Computation
title: Revenue for period
description: Recognized revenue for a date range.
status: stable
runtime: bigquery
parameters:
  - { name: start_date, type: date, required: true }
  - { name: end_date, type: date, required: true }
executor:
  resource: references/skills/run-on-bq.md
  receipt: [job_id, executed_sql, result]
attester:
  resource: references/attesters/revenue.py
generated: { by: test_agent/v1, at: 2026-01-10T12:00:00Z }
---

# Computation

    SELECT SUM(amount) AS revenue FROM sales.orders
    WHERE order_date BETWEEN @start_date AND @end_date
