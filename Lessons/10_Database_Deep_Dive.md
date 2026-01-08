# Lesson 10: Database Deep Dive - Advanced SQL Queries

This lesson teaches advanced SQL techniques for querying and analyzing your security analysis data. You will learn to write complex queries, perform aggregations, and extract insights from your database.

Prerequisites: Complete Lessons 01-06 (especially Lesson 06 on database schema)

---

## Code Modification Note

This lesson is read-only. You will be querying data, not modifying project code. No git branching needed.

---

## Learning Goals

By the end of this lesson, you will be able to:
- Write JOIN queries across multiple tables
- Perform aggregations (COUNT, AVG, GROUP BY)
- Analyze trends over time
- Find patterns in security findings
- Extract IOC frequency statistics
- Explain database query strategies in interviews
- Optimize query performance

---

## Your Database Schema (Quick Recap)

Your database has 5 tables with foreign key relationships:

```
analysis_runs (parent)
  findings (child)
  hypotheses (child)
  indicators_of_compromise (child)
  reports (child)
```

Schema defined at: src/storage.py

---

## Part 1: Basic Queries (Warm-Up)

### Setup: Open Your Database

```powershell
# Make sure you have run the pipeline at least once
python -m src.main --input data\evtx_parsed --model gpt-4o

# Open SQLite command line
sqlite3 db\analysis.db
```

Or use a GUI tool:
- DB Browser for SQLite (https://sqlitebrowser.org/)
- VS Code extension: SQLite Viewer

---

### Query 1: See All Analysis Runs

```sql
SELECT 
    run_id,
    model_used,
    status,
    datetime(timestamp, 'localtime') as run_time
FROM analysis_runs
ORDER BY timestamp DESC;
```

What you learn:
- How many times you have run the analysis
- Which models you used
- When each run happened
- Overall success vs partial/failed runs

---

### Query 2: Count Findings by Severity

```sql
SELECT 
    severity,
    COUNT(*) as count
FROM findings
GROUP BY severity
ORDER BY 
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        WHEN 'info' THEN 5
    END;
```

What you learn:
- Distribution of finding severities
- Overall risk profile

---

### Query 3: List All IOCs by Frequency

```sql
SELECT 
    indicator,
    COUNT(*) as occurrences
FROM indicators_of_compromise
GROUP BY indicator
ORDER BY occurrences DESC;
```

What you learn:
- Which IOCs appear most frequently
- Potential pivot points for investigation

---

## Part 2: JOIN Queries (Connecting Tables)

### Query 4: Findings with Their Run Context

```sql
SELECT 
    ar.run_id,
    datetime(ar.timestamp, 'localtime') as run_time,
    ar.model_used,
    f.severity,
    f.title,
    f.summary
FROM findings f
JOIN analysis_runs ar ON f.run_id = ar.run_id
WHERE f.severity IN ('critical', 'high')
ORDER BY ar.timestamp DESC, f.severity;
```

What you learn:
- Which runs produced which high-severity findings
- Timeline of critical/high severity discoveries

---

### Query 5: Complete Analysis Summary (All Tables)

```sql
SELECT 
    ar.run_id,
    datetime(ar.timestamp, 'localtime') as run_time,
    COUNT(DISTINCT f.finding_id) as finding_count,
    COUNT(DISTINCT h.hypothesis_id) as hypothesis_count,
    COUNT(DISTINCT ioc.ioc_id) as ioc_count
FROM analysis_runs ar
LEFT JOIN findings f ON ar.run_id = f.run_id
LEFT JOIN hypotheses h ON ar.run_id = h.run_id
LEFT JOIN indicators_of_compromise ioc ON ar.run_id = ioc.run_id
GROUP BY ar.run_id
ORDER BY ar.timestamp DESC;
```

What you learn:
- Complete overview of each analysis run
- Productivity of each run (findings/hypotheses/IOCs generated)

---

### Query 6: Findings with Evidence Count

```sql
SELECT 
    f.finding_id,
    f.severity,
    f.title,
    f.summary,
    json_array_length(f.evidence) as evidence_count
FROM findings f
ORDER BY f.severity;
```

What you learn:
- Which findings are strongly evidence-backed
- Where evidence is sparse

Note: evidence is stored as JSON in the evidence column.

---

## Part 3: Advanced Aggregations

### Query 7: Severity Distribution Over Time

```sql
SELECT 
    DATE(ar.timestamp) as analysis_date,
    f.severity,
    COUNT(*) as count
FROM findings f
JOIN analysis_runs ar ON f.run_id = ar.run_id
GROUP BY DATE(ar.timestamp), f.severity
ORDER BY analysis_date DESC, 
    CASE f.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        WHEN 'info' THEN 5
    END;
```

What you learn:
- How severity distribution changes day to day
- Trend analysis for reporting

---

### Query 8: Findings Per Run (Trend)

```sql
SELECT 
    ar.run_id,
    datetime(ar.timestamp, 'localtime') as run_time,
    COUNT(f.finding_id) as finding_count
FROM analysis_runs ar
LEFT JOIN findings f ON ar.run_id = f.run_id
GROUP BY ar.run_id
ORDER BY ar.timestamp DESC;
```

What you learn:
- Which runs generated more findings
- Potential spikes in suspicious activity

---

### Query 9: IOC Frequency Over Time

```sql
SELECT 
    DATE(ar.timestamp) as analysis_date,
    ioc.indicator,
    COUNT(*) as occurrences
FROM indicators_of_compromise ioc
JOIN analysis_runs ar ON ioc.run_id = ar.run_id
GROUP BY DATE(ar.timestamp), ioc.indicator
ORDER BY analysis_date DESC, occurrences DESC;
```

What you learn:
- IOCs that recur across multiple runs
- Indicators that are persistent over time

---

## Part 4: Investigative Queries

### Query 10: Recurring Findings Across Runs

```sql
SELECT 
    f.title,
    f.summary,
    COUNT(DISTINCT f.run_id) as appears_in_runs,
    GROUP_CONCAT(DISTINCT datetime(ar.timestamp, 'localtime')) as run_times
FROM findings f
JOIN analysis_runs ar ON f.run_id = ar.run_id
GROUP BY f.title, f.summary
HAVING COUNT(DISTINCT f.run_id) > 1
ORDER BY appears_in_runs DESC;
```

What you learn:
- Findings that appear across multiple runs
- Persistent or recurring issues

---

### Query 11: Hypotheses with Supporting Findings

```sql
SELECT 
    h.description,
    h.confidence,
    COUNT(DISTINCT f.finding_id) as supporting_findings,
    GROUP_CONCAT(DISTINCT f.severity) as severity_mix
FROM hypotheses h
JOIN findings f ON h.run_id = f.run_id
GROUP BY h.hypothesis_id
ORDER BY h.confidence DESC, supporting_findings DESC;
```

What you learn:
- Which hypotheses have the most supporting evidence
- Confidence vs evidence quantity

---

### Query 12: Findings with Most Evidence

```sql
SELECT 
    f.finding_id,
    f.title,
    f.severity,
    json_array_length(f.evidence) as evidence_count
FROM findings f
ORDER BY evidence_count DESC
LIMIT 10;
```

What you learn:
- Which findings are backed by the most evidence

---

### Query 13: IOCs Associated with High Severity Runs

```sql
SELECT 
    ioc.indicator,
    COUNT(DISTINCT f.finding_id) as associated_findings,
    COUNT(CASE WHEN f.severity = 'critical' THEN 1 END) as critical_findings,
    COUNT(CASE WHEN f.severity = 'high' THEN 1 END) as high_findings
FROM indicators_of_compromise ioc
JOIN findings f ON ioc.run_id = f.run_id
GROUP BY ioc.indicator
HAVING critical_findings > 0 OR high_findings > 0
ORDER BY critical_findings DESC, high_findings DESC, associated_findings DESC;
```

What you learn:
- Which IOCs correlate with the most severe findings

---

## Part 5: Performance Optimization

### Creating Indexes for Faster Queries

The schema does not create indexes by default, but you can add them for common query patterns:

```sql
CREATE INDEX IF NOT EXISTS idx_findings_severity 
ON findings(severity);

CREATE INDEX IF NOT EXISTS idx_findings_run_id 
ON findings(run_id);

CREATE INDEX IF NOT EXISTS idx_ioc_indicator 
ON indicators_of_compromise(indicator);
```

---

### Query Performance Analysis

Use EXPLAIN QUERY PLAN to see how SQLite executes your query:

```sql
EXPLAIN QUERY PLAN
SELECT * FROM findings
WHERE severity = 'critical';
```

---

## Interview Explanation: Database Query Strategy

Use a structured explanation:

- "My database uses analysis_runs as the parent table with child tables for findings, hypotheses, indicators_of_compromise, and reports."
- "For trend analysis, I join findings to analysis_runs and group by date and severity."
- "For prioritization, I look at recurring findings and IOCs associated with high severity runs."
- "For performance, I add indexes on run_id and severity and validate with EXPLAIN QUERY PLAN."

---

## Practice Exercises

1) Dashboard summary
- Total runs
- Total findings by severity
- Total IOCs
- Most recent run timestamp
- Average findings per run

2) Find outlier runs
- Runs with unusually high findings compared to average

3) Threat timeline
- Findings ordered by severity and evidence count for a given run

---

## Quick Reference: SQL Cheat Sheet

Aggregation:
```sql
COUNT(*), COUNT(DISTINCT col), AVG(col), MIN(col), MAX(col), GROUP_CONCAT(col)
```

Filtering:
```sql
WHERE col = 'value'
WHERE col LIKE '%pattern%'
WHERE col IN ('a', 'b')
WHERE col IS NULL
HAVING COUNT(*) > 5
```

Joining:
```sql
INNER JOIN
LEFT JOIN
```

Date Functions (SQLite):
```sql
DATE(timestamp)
datetime(timestamp, 'localtime')
strftime('%Y-%m-%d', timestamp)
```

---

## Next Steps

Continue with:
- Lesson 11: Interview Q and A Practice

---

## Additional Resources

- SQLite Documentation: https://www.sqlite.org/docs.html
- SQL Tutorial: https://www.sqlitetutorial.net/
- Practice: https://sqliteonline.com/
