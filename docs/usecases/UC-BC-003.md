# UC-BC-003 — Periodic beacon to SGB IP (NetFlow)

| Alan          | Deger |
|---------------|-------|
| ID            | UC-BC-003 |
| MITRE         | TA0011 / T1071, T1029 (Scheduled Transfer) |
| CT            | BC |
| Severity base | 8 |
| Data sources  | NetFlow, sFlow, IPFIX, firewall flow logs |
| Reference     | `SGB_BC_IP` |

## Detection logic

Tek bagantilara ek olarak, periyodik beacon paterni: ayni src->dst pair'i son
1 saatte >=5 esit araliki kucuk flow uretmis. SGB IP match + beacon paterni =
yuksek hassasiyetli botnet onaylama.

```
flow_count >= 5
  AND median_inter_arrival < 60s
  AND stddev(inter_arrival) < 20s
  AND dest_ip in SGB_BC_IP
  AND avg_bytes_per_flow < 4KB
```

## QRadar

- Flow Rule + custom property "Avg Flow Interval"
- Aggregator rule: "this rule matches at least 5 times in 1 hour on the same source IP and destination IP"

## Splunk

- Saved search: tstats / mstats ile flow indekslerinde
- `| stats avg(...) stdev(...) count by src_ip dest_ip | where ...`

## False positives

- SaaS heartbeat (Slack, Teams) - destination SGB_BC_IP'de olmayacak normalde, ama feed yanlislikla cloud IP icerirse -> review process
- Health-check probe'lari -> known monitoring src_ip exception
