# 3-Week Cloud & Data Pipeline Intuition Plan (GCP-Focused)

## Purpose
This document outlines a focused, time-bounded approach to building **cloud security and data pipeline intuition** sufficient for a senior-level technical interview, while compounding long-term AI Security Engineering skills.

The goal is **not mastery**.  
The goal is **credible reasoning about production systems**.

---

## Core Reframe
You are **not learning “cloud”**.

You are learning one specific slice:

> How security-relevant telemetry is generated, moved, transformed, and consumed.

Everything else is out of scope for now.

---

## The Three Non-Negotiable Mental Models

### 1. Cloud = Control Plane + Data Plane + Telemetry
- **Control Plane**: API calls, identity actions, configuration changes  
- **Data Plane**: Workloads, runtime behavior, traffic  
- **Telemetry**: Logs, metrics, traces emitted by both

Security investigations primarily rely on **control-plane logs and audit trails**, not raw packets.

---

### 2. Logs Move Through Pipelines (Not Magic)
All log systems follow the same lifecycle:

```
SOURCE → INGEST → PARSE → NORMALIZE → ENRICH → STORE → QUERY → ALERT/ANALYZE
          ↑                    ↑                                      ↑
    (Transport only)    (TRUST BOUNDARY)                     (AI belongs here)
```

**Critical Distinctions**:

- **Ingest** = Reliable movement into your system boundary
  - *Implementations*: Log Router, Collector, Sink, Forwarder
  - *Mental rule*: If it moves logs but doesn't interpret them, it's ingest
  
- **Parse** = Extract fields from raw text/JSON
  - Example: Extract `principalEmail` from JSON blob
  
- **Normalize** = Map fields to common schema
  - Example: Map `principalEmail` → `actor` (source-agnostic field name)
  - Why: Different sources call the same thing different names
  
- **Trust Boundary** = The line between untrusted and trusted data
  - **Before**: Source, Ingest, Parse (data is raw, potentially malicious)
  - **After**: Normalize, Enrich, Store, Analyze (data is structured, validated)
  - **Rule**: Never run AI on untrusted data

**Why This Matters**:
- Vendors differ. Architecture does not.
- If you can reason through this flow, you can reason about most security platforms.
- The trust boundary explains *why* ThreatPrism does deterministic parsing before AI analysis.

---

### 3. AI Belongs After Structure, Not Before
- Raw logs are noisy and ambiguous  
- **Parsing and normalization must come first**  
- **Trust boundary separates untrusted raw data from validated structured data**
- AI operates on **structured, scoped artifacts** *after* the trust boundary
- Evidence, traceability, and constraints are mandatory in security systems

**The Trust Boundary Rule**:
```
UNTRUSTED               | TRUSTED
Source → Ingest → Parse | Normalize → Enrich → Store → AI/Analysis
                            ↑                        ↑            ↑
                   TRUST BOUNDARY(TB)                TB           TB
                   Sanitize Data                Sanitize in       Sanitize out
                   Det Guard                    Det & Semantic    Policy,Det,Sem?

Never run AI before this line↑                                    
```

This aligns directly with the ThreatPrism design philosophy.

---

## Why GCP Is the Focus
- Repeatedly referenced by interviewer
- Clean, explicit audit logging model
- Clear IAM and identity semantics
- Faster path to intuition than broader platforms

---

## GCP Scope (Intentionally Narrow)

### 1. GCP Audit Logs (Primary Focus)
Understand:
- Admin Activity logs
- Data Access logs
- Actor, action, resource, timestamp, outcome

Key intuition:
> Most cloud security incidents reduce to “who did what, where, and when.”

---

### 2. IAM (Conceptual Only)
Focus on:
- Principals (users, service accounts)
- Roles vs permissions
- How identity appears in logs
- Why misconfiguration is a major risk vector

---

### 3. Log Routing / Sinks
Understand:
- Logs can be routed to multiple destinations
- Centralization is intentional
- Ingestion and analysis are decoupled by design

This mirrors SIEM architecture patterns.

---

### 4. Observability Tool: OpenObserve: https://openobserve.ai/
Purpose:
- Visualize a complete pipeline end-to-end
- See ingest, parse, store, query, and visualize in one system

Goal is **intuition**, not tool mastery.

---

## 3-Week Execution Plan (Detailed)

---

## Week 1 — Mental Models & Vocabulary

**Goal**: Become fluent enough to discuss cloud logs without confusion.

**Time Investment**: 5-7 hours across the week

---

### Day 1: Cloud Security Fundamentals (2 hours)

**Read** (in order):
1. [Cloud Audit Logs Overview](https://cloud.google.com/logging/docs/audit) - 20 min
   - Focus on: What gets logged, who, what, when, where
   - Skip: Advanced filtering, retention policies (for now)

2. [Understanding Cloud Identity](https://cloud.google.com/iam/docs/overview) - 15 min
   - Focus on: Principals (users, service accounts), roles
   - Why it matters: Every audit log has an identity

3. [Google Cloud Architecture Framework - Security](https://cloud.google.com/architecture/framework/security/logging-detection-response) - 25 min
   - Focus on: Detection and response section
   - Note patterns that mirror your ThreatPrism architecture

**Concrete Deliverable**:
Write 3-5 sentences answering: "What is a cloud audit log and why does it matter for security?"

**Example answer**:
> Cloud audit logs capture API calls and administrative actions in cloud environments. They record who (identity), did what (action), to which resource, when, and the outcome (success/failure). For security, they're the primary evidence trail for investigating unauthorized access, misconfigurations, and insider threats. Unlike traditional logs, they capture control plane events - the privileged operations that change infrastructure.

---

### Day 2: Anatomy of GCP Audit Logs (1.5 hours)

**Hands-On Exercise**:

1. Visit [Example Audit Log Entries](https://cloud.google.com/logging/docs/audit/understanding-audit-logs#example-entries)

2. Copy this example into a text editor:
```json
{
  "protoPayload": {
    "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
    "authenticationInfo": {
      "principalEmail": "user@example.com"
    },
    "requestMetadata": {
      "callerIp": "203.0.113.12"
    },
    "serviceName": "compute.googleapis.com",
    "methodName": "v1.compute.instances.insert",
    "resourceName": "projects/my-project/zones/us-central1-a/instances/my-instance",
    "request": {
      "@type": "type.googleapis.com/compute.instances.insert"
    }
  },
  "insertId": "abc123",
  "resource": {
    "type": "gce_instance",
    "labels": {
      "instance_id": "1234567890",
      "zone": "us-central1-a"
    }
  },
  "timestamp": "2024-01-15T10:23:45.678Z",
  "severity": "NOTICE"
}
```

3. **Dissect it** (fill in this table):

| Field | Value | Security Relevance |
|-------|-------|-------------------|
| **Actor** (Who) | user@example.com | Is this a legitimate user or service account? |
| **Action** (What) | v1.compute.instances.insert | Creating a VM - could be legit or crypto mining |
| **Resource** (Where) | my-instance in us-central1-a | Which asset was affected? |
| **Timestamp** (When) | 2024-01-15 10:23:45 | Outside business hours? Unusual timing? |
| **Source IP** | 203.0.113.12 | Lookup: Is this internal, VPN, or external? |
| **Outcome** | (not shown in this example) | Success or denied? Failed attempts = recon |

4. **Red Flag Analysis**:
   Write what would make this suspicious:
   - Source IP from Russia/China/unexpected country
   - User account that normally doesn't create VMs
   - Time: 3 AM on Sunday
   - Instance type: GPU-heavy (crypto mining pattern)

**Concrete Deliverable**:
Analyze 3 different example logs from the GCP docs and identify what makes each suspicious vs. benign.

---

### Day 3: IAM Security Patterns (1.5 hours)

**Focus**: Understanding privilege escalation in cloud

**Read**:
1. [IAM Best Practices](https://cloud.google.com/iam/docs/using-iam-securely) - 30 min
   - Focus on: Principle of least privilege, service account risks
   - Why: Most cloud breaches involve IAM misconfiguration

2. Study this attack pattern:
```
Attacker gains access to:
  → Service account with "Storage Object Viewer" role
  → Discovers bucket with Terraform state files
  → State files contain service account keys with Owner role
  → Privilege escalation complete
```

**Exercise**:
Map this to MITRE ATT&CK:
- Initial Access: Valid Accounts (T1078)
- Discovery: Cloud Infrastructure Discovery (T1580)
- Privilege Escalation: Valid Accounts (T1078.004)

**Concrete Deliverable**:
Write 1 paragraph explaining: "Why is IAM the most critical cloud security control?"

---

### Day 4-5: Vocabulary Drill & Synthesis (2 hours)

**Create Flashcards** (use Anki, Quizlet, or just index cards):

**Control Plane vs Data Plane**
- Q: What's the difference?
- A: Control plane = API calls that configure/manage resources. Data plane = actual workload traffic/operations

**Audit Log Types**
- Q: What are the 3 types of GCP audit logs?
- A: Admin Activity (always on), Data Access (opt-in), System Event (automated actions)

**Principal**
- Q: What is a principal in IAM?
- A: An identity that can perform actions: user, service account, group, or domain

**Service Account**
- Q: Why are service accounts dangerous?
- A: They're non-human identities with long-lived credentials, often over-privileged, and can be stolen from code/configs

**Log Router**
- Q: What does it do?
- A: Routes logs from Cloud Logging to destinations (Pub/Sub, BigQuery, Cloud Storage, external SIEM)

**Enrichment**
- Q: What is log enrichment?
- A: Adding context to raw logs: GeoIP, threat intel, user directory lookups, MITRE ATT&CK tags

**Severity Levels**
- Q: GCP log severity levels?
- A: DEFAULT, DEBUG, INFO, NOTICE, WARNING, ERROR, CRITICAL, ALERT, EMERGENCY

**Sink**
- Q: What's a sink in data pipelines?
- A: Final destination where processed data is stored (BigQuery, S3, Elasticsearch)

**Practice Interview Question**:
Record yourself answering: "Walk me through what happens when a user creates a VM in GCP from a security logging perspective."

**Good answer**:
> The user makes an API call to compute.googleapis.com. The Cloud IAM service checks if their identity has the compute.instances.create permission. If authorized, the VM is created and an Admin Activity audit log is automatically generated. This log contains the principal email, source IP, resource name, timestamp, and success status. The log flows to Cloud Logging, where a Log Router can send it to a sink like BigQuery for long-term analysis or Pub/Sub for real-time alerting. A security pipeline would enrich this log with GeoIP data, check if the user normally creates VMs, and flag anomalies like unusual instance types or regions.

**Week 1 Deliverable Checklist**:
- [ ] Written 1-paragraph explanations for audit logs and IAM
- [ ] Analyzed 3 example audit logs with red flag identification
- [ ] Created 8+ flashcards and can define all terms
- [ ] Recorded yourself answering the VM creation question
- [ ] Can explain to a friend/rubber duck: "Why cloud logs matter"

---

## Week 2 — Pipeline Intuition (Light Hands-On)

**Goal**: Understand why pipelines matter by seeing one work.

**Time Investment**: 6-8 hours

---

### Day 1: OpenObserve Setup (2 hours)

**What is OpenObserve**:
Lightweight, open-source observability platform. Think "mini-Splunk" you can run locally. You'll use it to SEE the pipeline stages, not master the tool.

**Installation**:

1. **Download** (Windows):
   ```powershell
   # Visit https://openobserve.ai/download
   # Or direct download:
   Invoke-WebRequest -Uri "https://github.com/openobserve/openobserve/releases/latest/download/openobserve-windows-amd64.zip" -OutFile "openobserve.zip"
   Expand-Archive openobserve.zip -DestinationPath C:\Tools\OpenObserve
   ```

2. **Run**:
   ```powershell
   cd C:\Tools\OpenObserve
   .\openobserve.exe
   ```
   - Opens on http://localhost:5080
   - Default credentials: admin / Complexpass#123

3. **Verify**:
   - Access web UI
   - See empty dashboard
   - Check "Logs" and "Streams" tabs

**Troubleshooting**:
- Port 5080 in use? Stop other services or change port: `.\openobserve.exe --http-port 5081`
- Firewall blocking? Allow in Windows Defender

**Concrete Deliverable**:
Screenshot of OpenObserve dashboard with your local instance running.

---

### Day 2: Ingest Sample Logs (2 hours)

**Create Test Data**:

1. Create a file: `C:\Projects\sample_logs\gcp_audit_sample.json`

```json
{"timestamp":"2025-12-19T10:15:00Z","severity":"NOTICE","principalEmail":"alice@company.com","sourceIp":"203.0.113.5","action":"storage.buckets.create","resource":"projects/my-project/buckets/sensitive-data","outcome":"success"}
{"timestamp":"2025-12-19T10:16:00Z","severity":"WARNING","principalEmail":"bob@company.com","sourceIp":"198.51.100.23","action":"compute.instances.create","resource":"projects/my-project/zones/us-east1/instances/crypto-miner","outcome":"success"}
{"timestamp":"2025-12-19T10:17:00Z","severity":"ERROR","principalEmail":"eve@external.com","sourceIp":"192.0.2.45","action":"iam.serviceAccounts.setIamPolicy","resource":"projects/my-project/serviceAccounts/admin-sa","outcome":"denied"}
{"timestamp":"2025-12-19T10:18:00Z","severity":"CRITICAL","principalEmail":"admin@company.com","sourceIp":"93.184.216.34","action":"storage.buckets.delete","resource":"projects/my-project/buckets/backup","outcome":"success"}
```

2. **Ingest via API**:
   ```powershell
   # OpenObserve ingestion endpoint
   $headers = @{
       "Authorization" = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:Complexpass#123"))
       "Content-Type" = "application/json"
   }
   
   Get-Content C:\Projects\sample_logs\gcp_audit_sample.json | ForEach-Object {
       Invoke-RestMethod -Uri "http://localhost:5080/api/default/security_logs/_json" -Method Post -Headers $headers -Body $_
   }
   ```

3. **Verify Ingestion**:
   - Go to OpenObserve UI → Logs
   - Select stream: `security_logs`
   - See 4 log entries

**Concrete Deliverable**:
Screenshot showing the 4 ingested logs in OpenObserve.

---

### Day 3: Parsing & Querying (2 hours)

**Explore Raw vs Parsed**:

1. **Query raw logs**:
   - In OpenObserve, go to Logs → Query
   - Search: `severity:CRITICAL`
   - Notice: You can query because OpenObserve auto-parsed JSON

2. **Understand Parse vs Normalize**:

**Parsing** = Extracting fields from raw format
```json
// Raw log (text or JSON blob)
{"protoPayload": {"authenticationInfo": {"principalEmail": "user@company.com"}}}

// After parsing (fields extracted)
{
  "principalEmail": "user@company.com",
  "methodName": "storage.buckets.create"
}
```

**Normalizing** = Mapping to common schema
```json
// After normalization (source-agnostic)
{
  "actor": "user@company.com",      // was principalEmail in GCP
  "action": "create_bucket",        // was methodName in GCP
  "source_type": "gcp_audit"
}
```

**Why this matters**:
- Parse = make queryable
- Normalize = make comparable across sources
- A Sysmon log and GCP log both have "actor" after normalization

3. **Compare to unparsed**:
   Create a file `raw_text.log`:
   ```
   Dec 19 10:15:00 server1 user alice from 203.0.113.5 created bucket sensitive-data success
   Dec 19 10:16:00 server1 user bob from 198.51.100.23 created instance crypto-miner success
   ```
   
   Try to query: "Show me all events from alice"
   - With parsed JSON: `principalEmail:"alice@company.com"` works
   - With raw text: You'd have to search full text, can't filter by field

**The Lesson**:
Parsing = converting unstructured text into structured fields that can be queried/analyzed.
Normalization = mapping those fields to a common vocabulary for cross-source analysis.

4. **Create Custom Query**:
   ```sql
   SELECT principalEmail, COUNT(*) as event_count
   FROM security_logs
   WHERE severity IN ('WARNING', 'CRITICAL')
   GROUP BY principalEmail
   ORDER BY event_count DESC
   ```

**Concrete Deliverable**:
Write 3 queries:
1. Find all failed actions (outcome = denied)
2. Find actions from external IPs (not company range)
3. Count events by severity level

**Also**: Write 3 sentences explaining the difference between parsing and normalizing.

---

### Day 4: Enrichment Simulation (1.5 hours)

**Manual Enrichment Exercise**:

Take the 4 sample logs and enrich them:

| Original Field | Enrichment | Result | Source |
|---------------|------------|--------|--------|
| sourceIp: 203.0.113.5 | GeoIP lookup | United States | [IPInfo.io](https://ipinfo.io) |
| sourceIp: 93.184.216.34 | GeoIP lookup | Russia | Manual lookup |
| action: storage.buckets.create | MITRE ATT&CK | T1530 (Data from Cloud Storage) | [ATT&CK Matrix](https://attack.mitre.org) |
| principalEmail: eve@external.com | Employee directory | NOT AN EMPLOYEE | Context knowledge |
| resource: crypto-miner | Naming pattern | Suspicious - crypto keyword | Pattern matching |

**Add enrichment fields**:
```json
{
  "timestamp":"2025-12-19T10:16:00Z",
  "severity":"WARNING",
  "principalEmail":"bob@company.com",
  "sourceIp":"198.51.100.23",
  "action":"compute.instances.create",
  "resource":"crypto-miner",
  "outcome":"success",
  "enriched": {
    "geo_country": "United States",
    "mitre_technique": "T1496",
    "risk_score": 85,
    "explanation": "VM name contains 'crypto-miner' keyword - possible resource abuse"
  }
}
```

**Concrete Deliverable**:
Create an enriched version of all 4 logs with at least 2 enrichment fields each.

---

### Day 5: Synthesis - Why Pipelines Matter (1 hour)

**Write a 1-page explanation** answering:

"An executive asks: 'Why can't we just dump all logs into a database and search them?' Explain why a pipeline is necessary."

**Your answer should cover**:
1. **Volume**: Millions of logs/day, can't store everything without filtering
2. **Structure**: Raw logs are text blobs, need parsing for field-based queries
3. **Trust**: Unvalidated data is unsafe, need trust boundary before enrichment
4. **Normalization**: Different sources need common schema for correlation
5. **Context**: Logs alone don't tell the story, need enrichment (GeoIP, threat intel)
6. **Speed**: Real-time alerts require streaming, not batch searches
7. **Cost**: Storing raw logs is expensive, filtering/compression saves money
8. **Accuracy**: Parsing errors caught early prevent bad analysis

**Concrete Example to Use**:
> "If we stored raw Sysmon logs as text, searching for 'show me all PowerShell executions from external IPs in Russia that ran outside business hours' would require full-text scanning of terabytes. With a pipeline: parsing extracts process name and IP, normalization maps fields to common schema, enrichment adds GeoIP and business hours context, and we cross the trust boundary knowing the data is validated. Storage in structured format allows indexed queries that return results in milliseconds instead of hours. More importantly, we never run AI analysis on raw, unvalidated data—it operates post-trust-boundary on artifacts we can audit and explain."

**Week 2 Deliverable Checklist**:
- [ ] OpenObserve running locally with screenshot
- [ ] 4 sample logs ingested and visible in UI
- [ ] 3 custom queries created and executed
- [ ] All 4 logs enriched with context fields
- [ ] 1-page "why pipelines matter" explanation written
- [ ] Can verbally explain: "What breaks when parsing fails?"

---

## Week 3 — Mapping to ThreatPrism + GCP Proof

**Goal**: Connect cloud concepts to your system + demonstrate GCP capability.

**Time Investment**: 8-10 hours

---

### Days 1-2: Conceptual Mapping (3 hours)

**Create an Architecture Mapping Document**:

Create file: `docs/ThreatPrism_Cloud_Extension_Design.md`

**Section 1: Current State**
```
ThreatPrism Phase 1 (Ingest):
- Source: Local EVTX files
- Ingest: Python script reads from filesystem
- Parse: evtx library converts to JSON
- Store: JSONL files in data/evtx_parsed/
```

**Section 2: Cloud Extension - GCP Audit Logs**
```
Extended Pipeline:
- Source:Extract fields from JSON (principalEmail, methodName, etc.)
- [TRUST BOUNDARY] ← Data is now validated
- Normalize: Map principalEmail → actor, methodName → action
- Enrich: Add GeoIP, MITRE ATT&CK tags, threat intel pulls logs
- Parse: Already JSON, validate schema
- Enrich: Add GeoIP, MITRE ATT&CK tags
- Store: Cloud Storage (raw) + BigQuery (structured)
- Analyze: Same LLM analysis logic (source-agnostic)
- Report: Same report generation
```

**Section 3: What Stays the Same**
- LLM analysis phase (Phase 2) - works on normalized JSON regardless of source
- Security pattern detection - MITRE framework applies universally
- Report format - analyst needs are the same
- Evidence chain - provenance still critical
 (Cloud Logging, CloudWatch, etc.)
- Parsing: Handle different raw formats (JSON, XML, syslog)
- **Normalization layer**: Map diverse sources to common schema (NEW)
- Storage: BigQuery/cloud databases instead of SQLite (scale)
- Real-time: Pub/Sub instead of batch files (streaming)ommon format
- Storage: BigQuery instead of SQLite (scale)
- Real-time: Pub/Sub instead of batch files

**Section 5: Normalization Schema**
```python
class NormalizedSecurityEvent:
    timestamp: datetime
    source_type: str  # "windows_evtx", "gcp_audit", "aws_cloudtrail"
    severity: str
    actor: str  # principal, user, identity
    action: str  # method, command, operation
    resource: str  # target of action
    outcome: str  # success, denied, error
    source_ip: str
    raw_data: dict  # preserve original for provenance
    enrichments: dict  # GeoIP, threat intel, MITRE tags
``` (post-trust-boundary)
- Source-agnostic analysis layer (works on normalized schema)
- Evidence preservation (raw data always available)
- Trust boundary enforced (validation before enrichment)esign**
- Maintains "AI after structure" principle
- Source-agnostic analysis layer
- Evidence preservation
- Scales to multiple log sources without rewriting core logic

**Concrete Deliverable**:
Complete the mapping document with all 6 sections. This becomes your interview talking point.

---

### Day 3: Interview Narrative Rehearsal (1 hour)

**Practice answering** (record yourself):

**Question 1**: "How would you extend ThreatPrism to handle cloud logs?"
 that operates post-trust-boundary. Currently, it ingests EVTX files, but the architecture supports any structured log source. To add GCP audit logs, I'd: (1) Add a cloud ingestion module using the Cloud Logging API, (2) Parse to extract JSON fields, (3) Cross the trust boundary with validation, (4) Create a normalization layer that maps GCP's schema to our common security event format—things like principalEmail becomes 'actor', methodName becomes 'action', (5) Route normalized events through the existing enrichment and LLM analysis phase unchanged, (6) Update the storage layer to use BigQuery for scale. The core insight—that AI operates on structured, validated data after the trust boundary—remains the same regardless of source. This is why ThreatPrism can extend to cloud, containers, network logs, or any future source without changing the analysis logic. The trust boundary is preserved: we never run AI on raw, unvalidated logs
**Good answer structure**:
> "ThreatPrism is designed with a source-agnostic analysis layer. Currently, it ingests EVTX files, but the architecture supports any structured log source. To add GCP audit logs, I'd: (1) Add a cloud ingestion module using the Cloud Logging API, (2) Create a normalization layer that maps GCP's JSON schema to our common security event format, (3) Route normalized events through the existing LLM analysis phase unchanged, (4) Update the storage layer to use BigQuery for scale. The core insight—that AI operates on structured, validated data—remains the same regardless of source. This is why ThreatPrism can extend to cloud, containers, network logs, or any future source without changing the analysis logic."

**Question 2**: "What's the difference between cloud logs and endpoint logs?"

**Good answer**:
> "Cloud logs primarily capture control plane events—API calls, identity actions, configuration changes. Endpoint logs like Sysmon capture data plane events—process execution, file access, network connections. Cloud logs answer 'who changed what infrastructure,' endpoint logs answer 'what malware is running.' Both are critical: cloud logs detect account compromise and misconfigurations, endpoint logs detect runtime threats. A complete security pipeline ingests both, normalizes them to a common schema, and correlates across sources. For example: a cloud log shows an attacker created a VM, endpoint logs from that VM show crypto mining malware execution."

**Question 3**: "Why not just send all logs to an LLM and ask it to find threats?"

**Good answer**:the trust boundary. First, LLMs are expensive—analyzing millions of raw logs would cost tens of thousands per day. Second, LLMs hallucinate—without structured constraints, they'll invent threats from malformed or ambiguous data. Third, legal and compliance require provenance—you can't defend 'the AI said so' in court when the input was unvalidated raw text. The correct approach respects the trust boundary: ingest, parse, validate, then cross into trusted territory where we normalize and enrich. Only after that do we apply AI to high-fidelity, structured artifacts. This is what ThreatPrism does: deterministic preprocessing ensures evidence integrity and crosses the trust boundary safely, then AI augments human analysis with explanations and MITRE mappings. The AI is a force multiplier operating on validated data, not a replacement for engineering rigor. We never run AI before the trust boundary—that would be operationally dangerous and forensically indefensible
> "Three reasons: cost, accuracy, and evidence. First, LLMs are expensive—analyzing millions of raw logs would cost tens of thousands per day. Second, LLMs hallucinate—without structured constraints, they'll invent threats. Third, legal and compliance require provenance—you can't defend 'the AI said so' in court. The correct approach is: parse to structure, filter noise, enrich with context, then apply AI to high-fidelity artifacts. This is what ThreatPrism does: deterministic preprocessing ensures evidence integrity, AI augments human analysis with explanations and MITRE mappings. The AI is a force multiplier, not a replacement for engineering rigor."

**Concrete Deliverable**:
Record 2-minute answers to all 3 questions. Listen back. Refine until confident.

---

### Days 4-5: Minimal Viable Cloud Proof (4-5 hours)

**Goal**: Deploy one working Cloud Function that proves GCP capability.

---

#### Step 1: GCP Account Setup (30 min)

1. **Create free tier account**:
   - Go to https://console.cloud.google.com
   - Sign in with Google account
   - Enable billing (you won't be charged if you stay in free tier)
   - Set budget alert at $5

2. **Create project**:
   - Project name: `threatprism-demo`
   - Project ID: `threatprism-demo-[random]` (must be unique)
   - Location: No organization

3. **Enable APIs**:
   - Cloud Logging API
   - Cloud Functions API
   - Cloud Storage API
   - Cloud Build API

4. **Install gcloud CLI**:
   ```powershell
   # Download from https://cloud.google.com/sdk/docs/install
   # Or use installer:
   (New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
   & $env:Temp\GoogleCloudSDKInstaller.exe
   ```

5. **Authenticate**:
   ```powershell
   gcloud auth login
   gcloud config set project threatprism-demo-[your-project-id]
   ```

---

#### Step 2: Create Cloud Storage Bucket (15 min)

```powershell
# Create bucket for log output
gsutil mb -l us-central1 gs://threatprism-audit-logs

# Verify
gsutil ls
```

---

#### Step 3: Write Cloud Function (45 min)

Create local directory:
```powershell
mkdir C:\Projects\gcp-audit-function
cd C:\Projects\gcp-audit-function
```

**File 1**: `main.py`
```python
import json
from datetime import datetime, timedelta
from google.cloud import logging_v2
from google.cloud import storage

def fetch_audit_logs(request):
    """
    Cloud Function that fetches GCP Audit Logs and stores them in Cloud Storage.
    Triggered manually via HTTP request.
    """
    # Initialize clients
    logging_client = logging_v2.Client()
    storage_client = storage.Client()
    
    # Configuration
    project_id = "threatprism-demo-[your-project-id]"  # CHANGE THIS
    bucket_name = "threatprism-audit-logs"
    
    # Fetch logs from last 1 hour
    filter_str = (
        'protoPayload."@type"="type.googleapis.com/google.cloud.audit.AuditLog" '
        'AND timestamp>"{}"'
    ).format((datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z")
    
    # Query logs
    logs = []
    for entry in logging_client.list_entries(filter_=filter_str, max_results=10):
        log_data = {
            "timestamp": entry.timestamp.isoformat(),
            "severity": entry.severity,
            "principal": entry.payload.get("authenticationInfo", {}).get("principalEmail"),
            "action": entry.payload.get("methodName"),
            "resource": entry.payload.get("resourceName"),
            "source_ip": entry.payload.get("requestMetadata", {}).get("callerIp"),
        }
        logs.append(log_data)
    
    # Store in Cloud Storage
    bucket = storage_client.bucket(bucket_name)
    blob_name = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(logs, indent=2))
    
    return {
        "status": "success",
        "logs_collected": len(logs),
        "stored_in": f"gs://{bucket_name}/{blob_name}"
    }
```

**File 2**: `requirements.txt`
```
google-cloud-logging==3.9.0
google-cloud-storage==2.14.0
```

---

#### Step 4: Deploy Cloud Function (30 min)

```powershell
# Deploy
gcloud functions deploy fetch-audit-logs `
    --runtime python311 `
    --trigger-http `
    --allow-unauthenticated `
    --entry-point fetch_audit_logs `
    --region us-central1

# Wait for deployment (2-3 minutes)
```

---

#### Step 5: Test & Verify (30 min)

1. **Trigger the function**:
   ```powershell
   # Get the function URL from deployment output, then:
   Invoke-WebRequest -Uri "https://us-central1-threatprism-demo-[project-id].cloudfunctions.net/fetch-audit-logs"
   ```

2. **Check Cloud Storage**:
   ```powershell
   gsutil ls gs://threatprism-audit-logs/
   gsutil cat gs://threatprism-audit-logs/audit_logs_*.json
   ```

3. **Screenshot evidence**:
   - GCP Console → Cloud Functions → fetch-audit-logs (deployed)
   - Cloud Storage → threatprism-audit-logs → audit_logs_*.json file
   - File contents showing JSON logs

---

#### Step 6: Document Learnings (45 min)

Create: `docs/GCP_Deployment_Reflection.md`

**Answer these questions**:
1. What was harder than expected? (IAM permissions? Deployment errors?)
2. What was easier? (Managed services? APIs?)
3. How does this compare to local development? (No servers to manage!)
4. What would you need for production? (Auth, monitoring, error handling, cost controls)
5. How does this fit ThreatPrism? (Cloud ingestion module proven viable)

**Example reflection**:
> The hardest part was getting IAM permissions right—the service account needed both Logging Viewer and Storage Object Creator roles. The easiest part was deployment: gcloud CLI handles everything. Compared to local dev, there's no server management, but debugging is harder without direct console access. For production, I'd need proper authentication (not --allow-unauthenticated), Cloud Monitoring for observability, error handling with retries, and cost alerts. This proves ThreatPrism can extend to cloud sources: the function pulls real GCP logs and stores them structured, ready for the existing analysis pipeline.

**Concrete Deliverable**:
- [ ] Cloud Function deployed successfully
- [ ] At least 1 JSON file in Cloud Storage with audit logs
- [ ] 3 screenshots: function deployed, storage bucket, log file contents
- [ ] Reflection document completed
- [ ] Can explain: "I deployed a Cloud Function that ingests GCP audit logs"

---

### Week 3 Final Checklist

- [ ] Architecture mapping document complete (6 sections)
- [ ] 3 interview questions recorded and refined
- [ ] GCP project created with billing alerts
- [ ] Cloud Function deployed and tested
- [ ] Audit logs successfully retrieved and stored
- [ ] 3 screenshots captured
- [ ] Reflection document written
- [ ] Can confidently say: "I have hands-on GCP experience"

---

## Success Metrics

You've completed the plan when you can:

**Week 1 Success**:
- Define audit log, principal, service account, enrichment without hesitation
- Look at a GCP audit log JSON and immediately identify actor, action, resource
- Explain why IAM is the most critical cloud security control

**Week 2 Success**:
- Demonstrate OpenObserve with real logs
- Write queries to find specific security events
- Explain why raw logs are unusable without parsing (with concrete example)

**Week 3 Success**:
- Show GCP Console screenshots of working Cloud Function
- Explain how ThreatPrism would extend to cloud (with architecture diagram)
- Answer "Do you have cloud experience?" with "Yes, I deployed to GCP and here's what I built"
's the difference between **parsing** and **normalizing**?
- What is the **trust boundary** and why does it matter?
- Why should AI not operate on raw logs?
- How do you add a new log source safely?
- What telemetry matters most during an incident at 3 a.m.?

**Bonus question**: "Walk me through the full pipeline for a GCP audit log from creation to AI analysis."

**Perfect answer structure**:
> "A user makes an API call (SOURCE). Cloud Logging captures it and Log Router sends it to Pub/Sub (INGEST). A Cloud Function extracts fields like principalEmail, methodName, timestamp (PARSE). We cross the trust boundary—data is now validated. The normalizer maps principalEmail to 'actor' in our common schema (NORMALIZE). Enrichment adds GeoIP, MITRE ATT&CK tags, threat intel (ENRICH). Structured event goes to BigQuery (STORE). Security analysts query for patterns (QUERY). High-severity events trigger AI analysis, which operates on structured, validated data to generate explanations and correlate with other events (ANALYZE). The AI never touches raw logs—it works post-trust-boundary on artifacts we can audit and explain."
---

## Interview Readiness Litmus Test

You are ready if you can confidently answer:

- Where do cloud security logs originate?
- What breaks when parsing is incorrect?
- Why should AI not operate on raw logs?
- How do you add a new log source safely?
- What telemetry matters most during an incident at 3 a.m.?

---

## Important Guardrail
Do **not** attempt to fully implement cloud ingestion right now.

Premature implementation:
- Increases risk
- Dilutes focus
- Adds stress
- Produces half-built systems

Senior engineers explain systems clearly **before** building them.

---

## End State
After completing this plan, you should be able to:
- Reason confidently about cloud security telemetry
- Explain data pipelines in plain language
- Defend architectural decisions in interviews
- Extend your system conceptually without over-engineering
- Point to working GCP deployment as proof of capability

This is the bridge between interview success and real-world AI Security Engineering.

---

## Integration with ThreatPrism Lessons

### Complementary Learning Tracks

The existing ThreatPrism lessons and this cloud plan are **mutually reinforcing**, not competing:

**ThreatPrism Track** (Understanding what you built):
- Teaches system architecture and implementation details
- Provides deep technical grounding
- Shows mastery of existing solution
- Answers "how does your system work?"

**Cloud Pipeline Track** (Building new intuition):
- Teaches production patterns and vocabulary
- Provides industry context
- Shows growth mindset and adaptability
- Answers "how would you extend this?"

### Recommended Blended Schedule

#### Week 1: Foundation
- **Mon/Wed/Fri**: Cloud mental models (2 hrs each)
  - GCP Audit Logs overview
  - IAM concepts
  - Log routing patterns
- **Tue/Thu**: ThreatPrism lessons (1-2 hrs each)
  - Lesson 01: Architecture Guide
  - Lesson 02: Understanding The Harness

**Why**: Build both vocabularies simultaneously. Architecture lessons help you see similarities between your system and cloud patterns.

---

#### Week 2: Pipeline Intuition + Technical Depth
- **Mon/Wed**: OpenObserve hands-on (2-3 hrs each)
  - Install and run locally
  - Ingest sample logs
  - Observe parsing effects
- **Tue/Thu/Sat**: ThreatPrism lessons (1-2 hrs each)
  - Lesson 03: Phase1 Ingest Deep Dive
  - Lesson 04: LLM Analysis Deep Dive
  - Lesson 10: Database Deep Dive

**Why**: Seeing OpenObserve's pipeline reinforces understanding of your own ingest/storage patterns. The deep-dive lessons give you technical credibility.

---

#### Week 3: Synthesis + Proof
- **Mon/Tue**: Conceptual mapping (2 hrs each)
  - Map cloud logs to ThreatPrism architecture
  - Document extension strategy
- **Wed/Thu**: Minimal GCP deployment (2-4 hrs)
  - Set up GCP account
  - Deploy Cloud Function
  - Test and screenshot
- **Fri/Weekend**: Interview prep (3-4 hrs)
  - Lesson 11: Interview Q&A Practice
  - Lesson 12: Demo Interview Guide
  - Practice explaining both systems

**Why**: Week 3 is about synthesis. You demonstrate you understand YOUR system deeply AND can extend it to cloud contexts.

---

### Interview Narrative (Post-Completion)

> "I built ThreatPrism to demonstrate AI-augmented security analysis with strong architectural principles. After your feedback on cloud experience, I studied GCP audit logging and data pipeline patterns. I deployed a Cloud Function that ingests GCP logs to prove I can work with cloud platforms. More importantly, I can now explain how ThreatPrism would extend architecturally—the ingestion layer would normalize multiple log sources, the LLM analysis phase would remain source-agnostic, and the evidence chain would maintain integrity regardless of whether logs come from EVTX files or cloud APIs. The core insight—that AI belongs after structure, not before—applies universally."

This shows:
- **Depth**: You know your system intimately
- **Growth**: You responded to feedback by learning new domains
- **Synthesis**: You can connect disparate concepts
- **Pragmatism**: You didn't over-engineer, you built intuition

---

### Which Lessons Are Critical vs Optional

#### Must-Do (Interview Essential)
1. ✅ **Lesson 01**: Architecture Guide — explains your design
2. ✅ **Lesson 11**: Interview Q&A Practice — direct prep
3. ✅ **Lesson 12**: Demo Interview Guide — rehearsal
4. ✅ **Cloud Plan Weeks 1-3** — addresses feedback gap

#### High-Value (Technical Credibility)
5. ✅ **Lesson 03**: Phase1 Ingest Deep Dive — shows data engineering thinking
6. ✅ **Lesson 04**: LLM Analysis Deep Dive — shows AI engineering depth
7. ✅ **Lesson 10**: Database Deep Dive — shows backend/storage knowledge

#### Optional (Time Permitting)
8. ⏸️ **Lesson 02**: Understanding The Harness — useful but less critical
9. ⏸️ **Lessons 05-09**: Validation, Reports, Hands-On customization — skip if time-constrained

---

### Time Budget Reality Check

**Conservative estimate** (for interview readiness):
- Cloud Plan: 15-20 hours over 3 weeks
- Critical ThreatPrism Lessons: 8-12 hours
- **Total**: 23-32 hours

**Realistic schedule**:
- 1.5-2 hours per weekday = 15-20 hrs/week
- 2-4 hours on weekends = 4-8 hrs/week
- **Total available**: 19-28 hrs/week

✅ **Conclusion**: You CAN do both tracks in 3 weeks, but it will be focused work. Prioritize the "Must-Do" lessons first, then add High-Value lessons as time permits.

---

### Guardrails

**Stop if**:
- You're spending >2 hours on one concept without progress
- You're not sleeping or feeling burned out
- The interview is in <1 week (switch to rehearsal only)

**Adapt by**:
- Cutting optional lessons
- Reducing cloud hands-on to just GCP account setup + reading
- Focusing solely on verbal explanations without code

Remember: **Confident reasoning beats half-finished implementation every time.**

---

## Next Action

1. **Choose your start date** (e.g., Monday)
2. **Block calendar** with 1.5-2 hr slots
3. **Begin with Lesson 01** + Cloud Week 1 reading in parallel
4. **Report progress** after Week 1 to adjust if needed

Ready to start?
