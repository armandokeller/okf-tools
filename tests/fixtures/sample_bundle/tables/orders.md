---
type: BigQuery Table
title: Customer Orders
description: One row per completed customer order.
resource: https://console.cloud.google.com/bigquery?p=demo&d=sales&t=orders
tags: [sales, orders]
generated: { by: test_agent/v1, at: 2026-01-10T12:00:00Z }
verified: { by: human:tester, at: 2026-01-11T09:00:00Z }
status: stable
stale_after: 2026-12-31
sources:
  - id: sales-handbook
    resource: https://example.com/sales-handbook
    title: Sales handbook
    author: human:tester
    usage_count: 42
    last_modified: 2026-01-01
usage_window: { from: 2026-01-01, to: 2026-01-31 }
---

# Schema

| Column      | Type   | Description                         |
|-------------|--------|--------------------------------------|
| order_id    | STRING | Unique order id                      |
| customer_id | STRING | FK to [customers](/tables/customers.md) |

# Notes

See also [a concept that does not exist](/tables/missing.md) for future work.
