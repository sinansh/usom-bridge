# UC-MC-001 — Mobile/VPN traffic to SGB Mobile C&C indicator

| Alan          | Deger |
|---------------|-------|
| ID            | UC-MC-001 |
| MITRE         | TA0011 / T1437 (Mobile: Application Layer Protocol) |
| CT            | MC |
| Severity base | 7 |
| Data sources  | Mobile VPN (Pulse, GlobalProtect), MDM (Intune, Workspace ONE), Mobile gateway |
| Reference     | `SGB_MC_IP`, `SGB_MC_DOMAIN`, `SGB_MC_URL` |

## Detection logic

Rule **yalniz** mobile-class log source'larda calismali; corporate
workstation'lar icin baska CT (BC/AC) yeterli. MDM device_id ile asset
korelasyonu yapilarak kullanici kimligi ile birlestirilebilir.

## QRadar

- Event Rule with log source group filter: `Log Source Group = "Mobile / MDM"`
- Match: `dest_ip in SGB_MC_IP OR query in SGB_MC_DOMAIN OR url in SGB_MC_URL`
- Action: severity 7, notify MDM admin + add device to `SGB_MC_DEVICES`

## Splunk

- Saved search: `SGB - UC-MC-001 - Mobile C2 indicator`
- index=mobile_vpn OR index=mdm OR sourcetype=intune ile sinirla

## False positives

- BYOD personal traffic VPN icine sizmissa false alarm uretebilir -> personal subnet exception
- Mobile apt simulation -> simulasyon device tag exception
