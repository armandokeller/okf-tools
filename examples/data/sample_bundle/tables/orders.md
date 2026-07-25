---
type: BigQuery Table
title: Customer Orders
description: One row per completed customer order.
tags: [sales, orders]
generated: { by: reference_agent/demo, at: 2026-01-10T12:00:00Z }
---

# Schema

| Column      | Type   | Description                              |
|-------------|--------|-------------------------------------------|
| order_id    | STRING | Unique order id                          |
| customer_id | STRING | FK to [customers](/tables/customers.md)  |

# Notes

This is example data shipped with okf-tools; it is not from a real system.
