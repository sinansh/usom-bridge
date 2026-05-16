# UC-BC-001 — SGB Botnet C&C Outbound Connection

| Alan          | Deger |
|---------------|-------|
| ID            | UC-BC-001 |
| Title         | Internal host -> SGB Botnet C&C IP outbound connection |
| MITRE         | TA0011 / T1071 (Application Layer Protocol C2) |
| Severity      | base=8 (CT=BC) → criticality 8+ ile 10 |
| Data sources  | Firewall (Palo Alto, Fortinet, Cisco ASA), NetFlow, Proxy |
| Reference     | `SGB_BC_IP` (set) + `SGB_IP_MAP` (zenginlestirme) |
| Response      | PB-BC-001 (host isolate, packet capture, IR ticket) |

## QRadar Rule

**Tip:** Flow Rule + Event Rule (ikisi de)

**Event side:**
```
when the event QID is one of the following: Firewall Permit, Proxy Allow
AND when any of these properties is contained in any of these reference sets:
    Destination IP -> SGB_BC_IP
AND when the source network is one of the following: Trusted
```

**Flow side:** ayni mantik, `destinationip` icin.

**Response:**
- Dispatch new event "SGB Botnet C2 Outbound"
- Magnitude severity: 8 → AQL action ile criticality lookup
- Annotate offense
- Add source IP -> `SGB_INFECTED_HOSTS` (TTL 7 gun)
- Forward to SOAR (webhook / syslog)

## Tuning

- BC base zaten yuksek; source IH olsa bile offense aç (botnet IP'leri IH'de
  bile guvenilir genelde).
- Cloud egress NAT'larini exception et: aksi halde tum bir gateway'i
  isolate edebilir.
