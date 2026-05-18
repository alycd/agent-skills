---
name: dns-checker
description: Check DNS records for a sending domain against tinyEmail's required DKIM, SPF, and DMARC configuration. Use when verifying customer email setup, checking DNS propagation, or diagnosing delivery issues. Triggers: "check dns", "verify dns", "dns check", "check dkim", "check spf", "check dmarc", "dns settings", "email dns".
---

# DNS Checker

Verifies that a customer's sending domain has the correct DKIM, SPF, and DMARC DNS records required by tinyEmail.

## Required records

### DKIM (2 CNAME records)

| Selector | Host | Expected value | Type |
|---|---|---|---|
| tec1 | `tec1._domainkey.{domain}` | `tec1.dkim.tinyemail.com` | CNAME |
| tec2 | `tec2._domainkey.{domain}` | `tec2.dkim.tinyemail.com` | CNAME |

### SPF (1 TXT record)

| Host | Must include | Type |
|---|---|---|
| `{domain}` | `include:_spf.tinyemail.com` | TXT |

Full expected value: `v=spf1 include:_spf.tinyemail.com -all`

### DMARC (1 TXT record)

| Host | Must start with | Type |
|---|---|---|
| `_dmarc.{domain}` | `v=DMARC1` | TXT |

Full expected value: `v=DMARC1; p=none; sp=none; rua=mailto:reports@dmarc.tiny-email.com; ruf=mailto:reports@dmarc.tiny-email.com; fo=1; rf=afrf; pct=100; ri=86400`

---

## Instructions

Given a domain (e.g. `mail.acme.com`), run the following checks in order using `dig`. Use `+short` for clean output.

### Step 1 — Check DKIM tec1

```bash
dig CNAME tec1._domainkey.{domain} +short
```

**Pass**: output contains `tec1.dkim.tinyemail.com`
**Fail**: empty, NXDOMAIN, or wrong value

### Step 2 — Check DKIM tec2

```bash
dig CNAME tec2._domainkey.{domain} +short
```

**Pass**: output contains `tec2.dkim.tinyemail.com`
**Fail**: empty, NXDOMAIN, or wrong value

### Step 3 — Check SPF

```bash
dig TXT {domain} +short
```

**Pass**: one of the TXT records contains `include:_spf.tinyemail.com`
**Fail**: no TXT record contains the include, or record is missing entirely

> Note: A domain may have multiple TXT records. Scan all of them — pass if any contains the required include.

### Step 4 — Check DMARC

```bash
dig TXT _dmarc.{domain} +short
```

**Pass**: output contains a record starting with `v=DMARC1`
**Fail**: no DMARC record found

### Step 5 — Report results

Output a clear summary table:

```
DNS Check Results for: {domain}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ DKIM tec1   tec1._domainkey.{domain} → tec1.dkim.tinyemail.com
✅ DKIM tec2   tec2._domainkey.{domain} → tec2.dkim.tinyemail.com
✅ SPF         {domain} includes include:_spf.tinyemail.com
❌ DMARC       _dmarc.{domain} — no record found
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3/4 checks passed. Action required: DMARC record missing.
```

For each failure, include:
- What was found (the actual DNS value, or "no record")
- What was expected
- The exact record the customer needs to add

### Step 6 — Determine overall result

- **All 4 pass** → DNS is correctly configured. Step is complete — mark done.
- **Any fail** → DNS not ready. Report failures. Do NOT mark the step done (for use in durable-workflow retry scenarios).
