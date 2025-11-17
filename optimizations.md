# GCP Cost Optimization Dashboard - Optimizations Guide

## Table of Contents
1. [SQL Query Optimization](#sql-query-optimization)
2. [Storage Optimization](#storage-optimization)
3. [Query Scheduling Optimization](#query-scheduling-optimization)
4. [ML Auto Scaling Optimization](#ml-auto-scaling-optimization)
5. [Simulators Logic](#simulators-logic)

---

## SQL Query Optimization

### Overview
The SQL Query Optimization module identifies and fixes inefficient SQL queries running on BigQuery, reducing data processing costs by optimizing query patterns. BigQuery charges $5 per TB of data processed, so reducing the amount of data scanned directly translates to cost savings.

### Bad Situations (Anti-Patterns We Detect)

#### 1. SELECT * Queries
**Problem**: Selecting all columns processes unnecessary data, especially in wide tables with hundreds of columns.

**Example - Bad**:
```sql
SELECT * 
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
LIMIT 1000;
```

**Cost Impact**: If the table has 50 columns but you only need 5, you're processing 10x more data than necessary.

**Estimated Waste**: 80-90% of data processing costs

#### 2. Missing WHERE Clauses
**Problem**: Scanning entire tables without filters processes all historical data unnecessarily.

**Example - Bad**:
```sql
SELECT tripduration, start_station_name
FROM `bigquery-public-data.new_york_citibike.citibike_trips`;
```

**Cost Impact**: Processing years of data when you might only need recent records.

**Estimated Waste**: 70-95% of data processing costs


#### 3. No Partition Filters
**Problem**: BigQuery tables are often partitioned by date. Not filtering on partition columns forces BigQuery to scan all partitions.

**Example - Bad**:
```sql
SELECT user_id, event_name
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`;
```

**Cost Impact**: Scanning 365 partitions instead of 1 day's partition.

**Estimated Waste**: 99% of data processing costs (if you only need 1 day out of 365)

#### 4. Unnecessary CROSS JOINs
**Problem**: CROSS JOINs create cartesian products, multiplying row counts exponentially.

**Example - Bad**:
```sql
SELECT a.trip_id, b.station_id
FROM `bigquery-public-data.new_york_citibike.citibike_trips` a
CROSS JOIN `bigquery-public-data.new_york_citibike.citibike_stations` b;
```

**Cost Impact**: If table A has 1M rows and table B has 1K rows, you're processing 1B rows instead of 1M.

**Estimated Waste**: 100x-1000x increase in data processing

#### 5. Redundant Subqueries
**Problem**: Nested subqueries that could be simplified or eliminated cause multiple scans of the same data.

**Example - Bad**:
```sql
SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM `bigquery-public-data.samples.natality`
  )
);
```

**Cost Impact**: Multiple layers of processing for no benefit.

**Estimated Waste**: 20-40% overhead


### Good Situations (Optimized Patterns)

#### 1. Specific Column Selection
**Solution**: Select only the columns you actually need.

**Example - Good**:
```sql
SELECT tripduration, start_station_name, end_station_name
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE starttime >= '2017-01-01'
LIMIT 1000;
```

**Cost Savings**: 80-90% reduction in bytes processed

#### 2. Effective WHERE Clauses
**Solution**: Add filters to limit the data scanned, especially on indexed or clustered columns.

**Example - Good**:
```sql
SELECT tripduration, start_station_name
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE starttime BETWEEN '2017-01-01' AND '2017-01-31'
  AND tripduration > 300;
```

**Cost Savings**: 70-95% reduction in bytes processed

#### 3. Partition Pruning
**Solution**: Always filter on partition columns (usually date fields) to scan only relevant partitions.

**Example - Good**:
```sql
SELECT user_id, event_name
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_20170801`
WHERE totals.visits > 1;
```

**Cost Savings**: 99%+ reduction when querying specific dates instead of all partitions

#### 4. Proper JOINs with Conditions
**Solution**: Use INNER JOIN or LEFT JOIN with proper ON conditions instead of CROSS JOIN.

**Example - Good**:
```sql
SELECT t.trip_id, s.name
FROM `bigquery-public-data.new_york_citibike.citibike_trips` t
INNER JOIN `bigquery-public-data.new_york_citibike.citibike_stations` s
  ON t.start_station_id = s.station_id
WHERE t.starttime >= '2017-01-01';
```

**Cost Savings**: 100x-1000x reduction in data processed


#### 5. Simplified Query Structure
**Solution**: Flatten unnecessary subqueries and use CTEs (Common Table Expressions) for clarity.

**Example - Good**:
```sql
WITH recent_births AS (
  SELECT year, state, births
  FROM `bigquery-public-data.samples.natality`
  WHERE year >= 2000
)
SELECT state, SUM(births) as total_births
FROM recent_births
GROUP BY state;
```

**Cost Savings**: 20-40% reduction through query optimization

### How AI Optimization Works

The AI Optimizer Service analyzes each query and applies these transformations:

1. **Column Analysis**: Identifies SELECT * and replaces with specific columns based on table schema
2. **Filter Injection**: Adds WHERE clauses based on common query patterns (date ranges, status filters)
3. **Partition Detection**: Identifies partitioned tables and adds partition filters
4. **JOIN Optimization**: Converts CROSS JOINs to proper INNER/LEFT JOINs with conditions
5. **Subquery Simplification**: Flattens nested queries and removes redundant layers

### Expected Cost Reduction

- **Typical Savings**: 50-80% reduction in bytes processed
- **Best Case**: 95%+ reduction (queries with SELECT * and no filters)
- **Minimum Savings**: 20-30% (already somewhat optimized queries)

---

## Storage Optimization

### Overview
The Storage Optimization module analyzes Google Cloud Storage (GCS) buckets and recommends storage class changes, deletion candidates, compression opportunities, and lifecycle policies to reduce storage costs.

### GCS Storage Classes and Pricing

| Storage Class | Price per GB/month | Best For | Minimum Storage Duration |
|--------------|-------------------|----------|-------------------------|
| STANDARD | $0.020 | Frequently accessed data | None |
| NEARLINE | $0.010 | Data accessed < once/month | 30 days |
| COLDLINE | $0.004 | Data accessed < once/quarter | 90 days |
| ARCHIVE | $0.0012 | Data accessed < once/year | 365 days |


### Bad Situations (Cost Waste Scenarios)

#### 1. Wrong Storage Class
**Problem**: Storing infrequently accessed data in STANDARD class.

**Example - Bad**:
- Bucket: `old-logs-2020`
- Size: 500 GB
- Storage Class: STANDARD
- Last Accessed: 18 months ago
- Monthly Cost: 500 GB × $0.020 = $10.00/month

**Cost Impact**: Paying 16x more than necessary for archived data.

**Estimated Waste**: $9.40/month per bucket (94% waste)

#### 2. Stale Data Not Deleted
**Problem**: Keeping temporary files, test data, or expired backups indefinitely.

**Example - Bad**:
- Bucket: `temp-processing-files`
- Size: 1 TB
- Purpose: Temporary ETL staging
- Files older than: 90 days still present
- Monthly Cost: 1000 GB × $0.020 = $20.00/month

**Cost Impact**: Paying for data that serves no purpose.

**Estimated Waste**: 100% of storage cost for stale files

#### 3. Uncompressed Files
**Problem**: Storing compressible data (logs, JSON, CSV) without compression.

**Example - Bad**:
- Bucket: `application-logs`
- Size: 2 TB (uncompressed text logs)
- Compression Ratio: Could be 5:1
- Monthly Cost: 2000 GB × $0.020 = $40.00/month

**Cost Impact**: Paying 5x more for storage than necessary.

**Estimated Waste**: $32.00/month (80% waste)

#### 4. No Lifecycle Policies
**Problem**: Manual management of storage classes and deletions, leading to forgotten optimizations.

**Example - Bad**:
- Bucket: `user-uploads`
- No automatic transitions
- No automatic deletions
- Growing indefinitely

**Cost Impact**: Continuous cost increase without optimization.

**Estimated Waste**: 40-70% of total storage costs


#### 5. Cross-Region Storage
**Problem**: Storing data in expensive regions when cheaper regions would suffice.

**Example - Bad**:
- Bucket: `backup-data`
- Region: us-east1 (premium region)
- Access Pattern: Rarely accessed
- Could use: us-central1 (standard region)

**Cost Impact**: 10-20% higher storage costs.

**Estimated Waste**: $2-4/month per TB

### Good Situations (Optimized Storage)

#### 1. Appropriate Storage Class
**Solution**: Move infrequently accessed data to NEARLINE, COLDLINE, or ARCHIVE.

**Example - Good**:
- Bucket: `old-logs-2020`
- Size: 500 GB
- Storage Class: ARCHIVE
- Last Accessed: 18 months ago
- Monthly Cost: 500 GB × $0.0012 = $0.60/month

**Cost Savings**: $9.40/month (94% reduction)

#### 2. Automated Deletion Policies
**Solution**: Implement lifecycle rules to delete temporary or expired data.

**Example - Good**:
```json
{
  "lifecycle": {
    "rule": [{
      "action": {"type": "Delete"},
      "condition": {
        "age": 90,
        "matchesPrefix": ["temp/", "staging/"]
      }
    }]
  }
}
```

**Cost Savings**: 100% of stale data costs eliminated

#### 3. Compression Enabled
**Solution**: Compress text-based files before storage.

**Example - Good**:
- Bucket: `application-logs`
- Size: 400 GB (compressed with gzip)
- Original Size: 2 TB
- Monthly Cost: 400 GB × $0.020 = $8.00/month

**Cost Savings**: $32.00/month (80% reduction)


#### 4. Lifecycle Policies Configured
**Solution**: Automatic transitions between storage classes based on age.

**Example - Good**:
```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 30}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 90}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "ARCHIVE"},
        "condition": {"age": 365}
      }
    ]
  }
}
```

**Cost Savings**: 40-70% reduction over time as data ages

#### 5. Regional Optimization
**Solution**: Store data in cost-effective regions based on access patterns.

**Example - Good**:
- Bucket: `backup-data`
- Region: us-central1 (standard region)
- Access Pattern: Rarely accessed
- Storage Class: COLDLINE

**Cost Savings**: 10-20% on storage, plus reduced egress costs

### How AI Optimization Works

The AI Optimizer Service analyzes bucket metadata and provides:

1. **Access Pattern Analysis**: Identifies last access time and recommends appropriate storage class
2. **Deletion Candidates**: Flags buckets with "temp", "test", "staging" patterns or very old data
3. **Compression Detection**: Identifies text-based file types (logs, JSON, CSV) that could be compressed
4. **Lifecycle Recommendations**: Suggests automated policies based on bucket purpose and access patterns
5. **Cost Calculation**: Estimates monthly savings for each recommendation

### Expected Cost Reduction

- **Storage Class Changes**: 50-94% savings per bucket
- **Deletion of Stale Data**: 100% savings on deleted data
- **Compression**: 60-80% savings on compressible data
- **Overall Average**: 40-70% reduction in total storage costs

---

## Query Scheduling Optimization

### Overview
The Query Scheduling Optimization module analyzes BigQuery scheduled queries and identifies redundant schedules, over-frequent queries, merge opportunities, and materialized view candidates to reduce query execution costs.


### Bad Situations (Scheduling Waste)

#### 1. Over-Frequent Queries
**Problem**: Running queries more often than data updates or business needs require.

**Example - Bad**:
- Query: `daily_sales_summary`
- Schedule: Every 5 minutes (`*/5 * * * *`)
- Data Updates: Once per hour
- Cost per Run: $0.50
- Daily Cost: 288 runs × $0.50 = $144.00/day

**Cost Impact**: Running 288 times when 24 times would suffice.

**Estimated Waste**: $132.00/day (91.7% waste)

#### 2. Redundant Queries
**Problem**: Multiple scheduled queries computing similar or overlapping results.

**Example - Bad**:
- Query 1: `sales_by_region` (hourly)
- Query 2: `sales_by_country` (hourly)
- Query 3: `sales_by_city` (hourly)
- All queries scan the same base table with different GROUP BY clauses

**Cost Impact**: Scanning the same data 3 times instead of once.

**Estimated Waste**: 66% of total query costs

#### 3. No Materialized Views
**Problem**: Repeatedly computing the same aggregations instead of caching results.

**Example - Bad**:
- Query: `user_activity_summary`
- Schedule: Every hour
- Computation: Aggregates 1 TB of raw events each time
- Cost per Run: $5.00
- Daily Cost: 24 × $5.00 = $120.00/day

**Cost Impact**: Recomputing from scratch when incremental updates would work.

**Estimated Waste**: $100.00/day (83% waste)

#### 4. Queries Running During Peak Hours
**Problem**: Running non-urgent queries during business hours when resources are expensive.

**Example - Bad**:
- Query: `monthly_report_prep`
- Schedule: 9:00 AM daily (peak business hours)
- Could Run: 2:00 AM (off-peak)

**Cost Impact**: Higher slot costs during peak demand.

**Estimated Waste**: 20-30% premium on query costs


#### 5. Queries Without Incremental Logic
**Problem**: Full table scans on every run instead of processing only new data.

**Example - Bad**:
```sql
-- Runs every hour, scans all historical data
SELECT DATE(timestamp) as date, COUNT(*) as events
FROM `project.dataset.events`
GROUP BY date;
```

**Cost Impact**: Processing 1 year of data to update 1 hour of results.

**Estimated Waste**: 99%+ of data processing

### Good Situations (Optimized Scheduling)

#### 1. Right-Sized Frequency
**Solution**: Align query frequency with data update frequency and business needs.

**Example - Good**:
- Query: `daily_sales_summary`
- Schedule: Every hour (`0 * * * *`)
- Data Updates: Once per hour
- Cost per Run: $0.50
- Daily Cost: 24 runs × $0.50 = $12.00/day

**Cost Savings**: $132.00/day (91.7% reduction)

#### 2. Merged Queries
**Solution**: Combine related queries into a single query with multiple outputs.

**Example - Good**:
```sql
-- Single query replacing 3 separate queries
WITH sales_data AS (
  SELECT region, country, city, amount
  FROM `project.dataset.sales`
  WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
)
SELECT 
  region, SUM(amount) as total
FROM sales_data
GROUP BY region
UNION ALL
SELECT 
  country, SUM(amount) as total
FROM sales_data
GROUP BY country
UNION ALL
SELECT 
  city, SUM(amount) as total
FROM sales_data
GROUP BY city;
```

**Cost Savings**: 66% reduction (1 scan instead of 3)


#### 3. Materialized Views
**Solution**: Use materialized views for frequently computed aggregations.

**Example - Good**:
```sql
-- Create materialized view (one-time cost)
CREATE MATERIALIZED VIEW `project.dataset.user_activity_summary`
AS
SELECT 
  user_id,
  DATE(timestamp) as date,
  COUNT(*) as events,
  SUM(duration) as total_duration
FROM `project.dataset.events`
GROUP BY user_id, date;

-- Scheduled query now just reads the materialized view
SELECT * FROM `project.dataset.user_activity_summary`
WHERE date = CURRENT_DATE();
```

**Cost Savings**: $100.00/day (83% reduction) - only incremental updates needed

#### 4. Off-Peak Scheduling
**Solution**: Schedule non-urgent queries during off-peak hours.

**Example - Good**:
- Query: `monthly_report_prep`
- Schedule: 2:00 AM daily (`0 2 * * *`)
- Off-peak discount applied

**Cost Savings**: 20-30% reduction in query costs

#### 5. Incremental Processing
**Solution**: Process only new data since last run using timestamps or watermarks.

**Example - Good**:
```sql
-- Runs every hour, processes only last hour of data
DECLARE last_run TIMESTAMP DEFAULT (
  SELECT MAX(processed_until) FROM `project.dataset.watermarks`
  WHERE job_name = 'hourly_events'
);

INSERT INTO `project.dataset.events_summary`
SELECT DATE(timestamp) as date, COUNT(*) as events
FROM `project.dataset.events`
WHERE timestamp > last_run
  AND timestamp <= CURRENT_TIMESTAMP()
GROUP BY date;

-- Update watermark
UPDATE `project.dataset.watermarks`
SET processed_until = CURRENT_TIMESTAMP()
WHERE job_name = 'hourly_events';
```

**Cost Savings**: 99%+ reduction in data processed per run


### How AI Optimization Works

The AI Optimizer Service analyzes scheduled queries and provides:

1. **Frequency Analysis**: Compares CRON schedule with typical data update patterns
2. **Redundancy Detection**: Identifies queries with similar purposes or overlapping data scans
3. **Merge Opportunities**: Suggests combining queries that scan the same base tables
4. **Materialized View Candidates**: Identifies repeated aggregations that could be cached
5. **Time Optimization**: Recommends off-peak scheduling for non-urgent queries
6. **Incremental Logic**: Suggests watermark-based processing for large tables

### Expected Cost Reduction

- **Frequency Adjustments**: 50-90% reduction per over-frequent query
- **Query Merging**: 50-75% reduction for redundant queries
- **Materialized Views**: 70-90% reduction for repeated aggregations
- **Off-Peak Scheduling**: 20-30% reduction
- **Overall Average**: 40-70% reduction in scheduled query costs

---

## ML Auto Scaling Optimization

### Overview
The ML Auto Scaling Optimization module analyzes machine learning training jobs on Google Cloud and recommends compute optimizations including spot VMs, machine type changes, autoscaling configurations, and accelerator optimizations to reduce training costs.

### GCP ML Compute Pricing (Approximate)

| Resource Type | On-Demand Price | Spot Price | Spot Savings |
|--------------|----------------|------------|--------------|
| n1-standard-4 (CPU) | $0.19/hour | $0.04/hour | 79% |
| n1-highmem-8 (CPU) | $0.47/hour | $0.10/hour | 79% |
| NVIDIA T4 GPU | $0.35/hour | $0.11/hour | 69% |
| NVIDIA V100 GPU | $2.48/hour | $0.74/hour | 70% |
| NVIDIA A100 GPU | $3.67/hour | $1.10/hour | 70% |
| TPU v3 | $8.00/hour | $2.40/hour | 70% |


### Bad Situations (ML Training Waste)

#### 1. Using On-Demand VMs
**Problem**: Running training jobs on on-demand instances instead of spot/preemptible VMs.

**Example - Bad**:
- Job: `image_classification_training`
- Instance: 4x NVIDIA V100 GPUs (on-demand)
- Training Duration: 48 hours
- Cost: 4 × $2.48 × 48 = $475.20

**Cost Impact**: Paying 3x more than necessary for interruptible workloads.

**Estimated Waste**: $316.80 (67% waste)

#### 2. Over-Provisioned Machine Types
**Problem**: Using more powerful machines than the workload requires.

**Example - Bad**:
- Job: `small_model_training`
- Instance: n1-highmem-32 (32 vCPUs, 208 GB RAM)
- Actual Usage: 8 vCPUs, 30 GB RAM
- Training Duration: 24 hours
- Cost: $1.88 × 24 = $45.12

**Cost Impact**: Paying for 4x more resources than needed.

**Estimated Waste**: $33.84 (75% waste)

#### 3. No Autoscaling
**Problem**: Fixed cluster size even when training phases have varying resource needs.

**Example - Bad**:
- Job: `distributed_training`
- Cluster: 10 nodes (fixed)
- Peak Usage: 10 nodes (20% of time)
- Average Usage: 3 nodes (80% of time)
- Training Duration: 100 hours
- Cost: 10 × $0.19 × 100 = $190.00

**Cost Impact**: Paying for idle nodes during low-utilization phases.

**Estimated Waste**: $133.00 (70% waste)

#### 4. Wrong Accelerator Type
**Problem**: Using expensive GPUs for workloads that could run on cheaper alternatives.

**Example - Bad**:
- Job: `inference_optimization`
- Accelerator: 8x NVIDIA A100 GPUs
- Workload: Could run on T4 GPUs
- Training Duration: 12 hours
- Cost: 8 × $3.67 × 12 = $352.32

**Cost Impact**: Using premium GPUs when standard GPUs suffice.

**Estimated Waste**: $302.16 (86% waste)


#### 5. No Checkpointing
**Problem**: Not saving checkpoints, so spot VM interruptions require full restart.

**Example - Bad**:
- Job: `long_training_job`
- Instance: Spot VMs (can be interrupted)
- No checkpointing enabled
- Interruption at 80% completion
- Result: Restart from 0%, wasting 80% of compute

**Cost Impact**: Wasted compute on interrupted jobs.

**Estimated Waste**: 30-50% of spot VM costs due to restarts

#### 6. Inefficient Data Loading
**Problem**: Training bottlenecked by slow data loading, leaving GPUs idle.

**Example - Bad**:
- Job: `vision_model_training`
- GPU Utilization: 40% (waiting for data)
- Training Duration: 50 hours
- Effective Training Time: 20 hours
- Cost: 4 × $2.48 × 50 = $496.00

**Cost Impact**: Paying for 30 hours of idle GPU time.

**Estimated Waste**: $297.60 (60% waste)

### Good Situations (Optimized ML Training)

#### 1. Spot/Preemptible VMs
**Solution**: Use spot VMs for fault-tolerant training workloads.

**Example - Good**:
- Job: `image_classification_training`
- Instance: 4x NVIDIA V100 GPUs (spot)
- Training Duration: 48 hours
- Cost: 4 × $0.74 × 48 = $142.08

**Cost Savings**: $333.12 (70% reduction)

#### 2. Right-Sized Machine Types
**Solution**: Match machine type to actual resource requirements.

**Example - Good**:
- Job: `small_model_training`
- Instance: n1-highmem-8 (8 vCPUs, 52 GB RAM)
- Actual Usage: 8 vCPUs, 30 GB RAM
- Training Duration: 24 hours
- Cost: $0.47 × 24 = $11.28

**Cost Savings**: $33.84 (75% reduction)


#### 3. Autoscaling Enabled
**Solution**: Configure cluster autoscaling to match resource needs dynamically.

**Example - Good**:
- Job: `distributed_training`
- Cluster: 2-10 nodes (autoscaling)
- Peak Usage: 10 nodes (20% of time) = 20 hours
- Average Usage: 3 nodes (80% of time) = 80 hours
- Training Duration: 100 hours
- Cost: (10 × $0.19 × 20) + (3 × $0.19 × 80) = $38.00 + $45.60 = $83.60

**Cost Savings**: $106.40 (56% reduction)

#### 4. Appropriate Accelerator Type
**Solution**: Match GPU/TPU type to workload requirements.

**Example - Good**:
- Job: `inference_optimization`
- Accelerator: 8x NVIDIA T4 GPUs
- Workload: Inference and light training
- Training Duration: 12 hours
- Cost: 8 × $0.35 × 12 = $33.60

**Cost Savings**: $318.72 (90% reduction)

#### 5. Checkpointing Enabled
**Solution**: Save checkpoints regularly to resume from interruptions.

**Example - Good**:
```python
# Training script with checkpointing
checkpoint_callback = ModelCheckpoint(
    dirpath='gs://bucket/checkpoints',
    save_top_k=3,
    every_n_epochs=1
)

trainer = Trainer(
    callbacks=[checkpoint_callback],
    resume_from_checkpoint='gs://bucket/checkpoints/last.ckpt'
)
```

**Cost Savings**: 30-50% reduction in wasted compute from interruptions

#### 6. Optimized Data Pipeline
**Solution**: Use efficient data loading with prefetching and caching.

**Example - Good**:
```python
# Optimized data loading
dataset = tf.data.Dataset.from_tensor_slices(data)
dataset = dataset.cache()  # Cache in memory
dataset = dataset.prefetch(tf.data.AUTOTUNE)  # Prefetch next batch
dataset = dataset.batch(batch_size)
```

**Result**:
- GPU Utilization: 95%
- Training Duration: 21 hours (vs 50 hours)
- Cost: 4 × $2.48 × 21 = $208.32

**Cost Savings**: $287.68 (58% reduction)


### How AI Optimization Works

The AI Optimizer Service analyzes ML training jobs and provides:

1. **Spot VM Recommendations**: Identifies fault-tolerant jobs that can use spot instances
2. **Machine Type Analysis**: Compares actual resource usage to provisioned capacity
3. **Autoscaling Suggestions**: Analyzes utilization patterns and recommends scaling policies
4. **Accelerator Optimization**: Matches workload characteristics to appropriate GPU/TPU types
5. **Checkpointing Validation**: Ensures spot VM jobs have checkpoint mechanisms
6. **Data Pipeline Analysis**: Identifies GPU idle time caused by data loading bottlenecks

### Expected Cost Reduction

- **Spot VMs**: 60-70% savings on compute costs
- **Right-Sizing**: 40-75% savings on over-provisioned resources
- **Autoscaling**: 40-60% savings on idle capacity
- **Accelerator Optimization**: 50-90% savings from using appropriate GPU types
- **Overall Average**: 50-80% reduction in ML training costs

---

## Simulators Logic

### Overview
Simulators generate realistic synthetic data that mimics real-world GCP workloads. This allows the dashboard to demonstrate optimization capabilities without requiring access to actual enterprise data.

### 1. SQL Query Simulator

**Purpose**: Generate unoptimized SQL queries with common anti-patterns for BigQuery public datasets.

**Logic Flow**:

```
1. Input: Dataset name, table name, count (default 10)
2. Fetch table schema from BigQuery API
3. For each query to generate:
   a. Randomly select an anti-pattern type:
      - SELECT * (40% probability)
      - Missing WHERE clause (30% probability)
      - No partition filter (20% probability)
      - CROSS JOIN (5% probability)
      - Redundant subquery (5% probability)
   
   b. Generate query based on anti-pattern:
      - SELECT *: Use all columns, no filters
      - Missing WHERE: Select specific columns but no filters
      - No partition: Query wildcard table without date filter
      - CROSS JOIN: Join two tables without ON condition
      - Redundant subquery: Wrap query in unnecessary nested SELECT
   
   c. Add realistic but inefficient patterns:
      - Large LIMIT values (10000+)
      - ORDER BY without LIMIT
      - COUNT(*) on entire table
      - String operations on large text fields
4. Return list of unoptimized query strings
```


**Example Output**:

```python
[
    # Anti-pattern: SELECT *
    "SELECT * FROM `bigquery-public-data.new_york_citibike.citibike_trips` LIMIT 10000",
    
    # Anti-pattern: Missing WHERE
    "SELECT tripduration, start_station_name FROM `bigquery-public-data.new_york_citibike.citibike_trips`",
    
    # Anti-pattern: No partition filter
    "SELECT user_id, event_name FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`",
    
    # Anti-pattern: CROSS JOIN
    """SELECT t.trip_id, s.station_id 
       FROM `bigquery-public-data.new_york_citibike.citibike_trips` t 
       CROSS JOIN `bigquery-public-data.new_york_citibike.citibike_stations` s""",
    
    # Anti-pattern: Redundant subquery
    """SELECT * FROM (
         SELECT * FROM (
           SELECT year, state, births FROM `bigquery-public-data.samples.natality`
         )
       )"""
]
```

**Key Features**:
- Uses actual BigQuery public datasets for realistic dry-run costs
- Generates syntactically valid SQL that will execute
- Ensures variety of anti-patterns across generated queries
- Includes table schema awareness for column selection

### 2. Storage Simulator

**Purpose**: Generate synthetic GCS bucket metadata with realistic characteristics.

**Logic Flow**:

```
1. Input: Count (default 10)
2. Define bucket name patterns:
   - Production: "prod-data", "production-logs", "app-storage"
   - Backup: "backup-2020", "archive-data", "old-snapshots"
   - Temporary: "temp-processing", "staging-files", "test-data"
   - Logs: "application-logs", "access-logs", "audit-logs"

3. For each bucket to generate:
   a. Select bucket type (production, backup, temp, logs)
   
   b. Generate size based on type:
      - Production: 100 GB - 5 TB (normal distribution, mean 1 TB)
      - Backup: 500 GB - 10 TB (normal distribution, mean 3 TB)
      - Temporary: 50 GB - 2 TB (normal distribution, mean 500 GB)
      - Logs: 200 GB - 8 TB (normal distribution, mean 2 TB)
   
   c. Generate last_accessed date based on type:
      - Production: 1-30 days ago (recent)
      - Backup: 180-730 days ago (old)
      - Temporary: 60-180 days ago (stale)
      - Logs: 90-365 days ago (archived)
   
   d. Assign storage class (often wrong for cost waste):
      - 70% STANDARD (even for old data)
      - 15% NEARLINE
      - 10% COLDLINE
      - 5% ARCHIVE
   
   e. Select region:
      - us-central1, us-east1, us-west1, europe-west1, asia-east1
   
   f. Add metadata:
      - file_count: Random 1000-1000000
      - avg_file_size_mb: Calculated from total size
      - compression: "none" for 80%, "gzip" for 20%

4. Return list of bucket metadata dictionaries
```


**Example Output**:

```python
[
    {
        "name": "backup-2020-q1",
        "size_gb": 2500.0,
        "last_accessed": "2023-03-15",  # 20 months ago
        "region": "us-central1",
        "storage_class": "STANDARD",  # Should be ARCHIVE
        "file_count": 125000,
        "avg_file_size_mb": 20.48,
        "compression": "none",
        "purpose": "backup"
    },
    {
        "name": "temp-processing-files",
        "size_gb": 800.0,
        "last_accessed": "2023-08-20",  # 15 months ago
        "region": "us-east1",
        "storage_class": "STANDARD",  # Should be deleted
        "file_count": 50000,
        "avg_file_size_mb": 16.38,
        "compression": "none",
        "purpose": "temporary"
    },
    {
        "name": "application-logs-2024",
        "size_gb": 3200.0,
        "last_accessed": "2024-06-10",  # 5 months ago
        "region": "us-west1",
        "storage_class": "STANDARD",  # Should be COLDLINE + compressed
        "file_count": 800000,
        "avg_file_size_mb": 4.10,
        "compression": "none",  # Text logs should be compressed
        "purpose": "logs"
    }
]
```

**Key Features**:
- Realistic size distributions based on bucket type
- Intentionally suboptimal storage classes to demonstrate savings
- Access patterns that suggest optimization opportunities
- Metadata sufficient for AI analysis

### 3. Schedule Simulator

**Purpose**: Generate scheduled query metadata with various CRON patterns and cost characteristics.

**Logic Flow**:

```
1. Input: Count (default 10)
2. Define query purpose categories:
   - Analytics: "daily_sales_summary", "user_activity_report"
   - ETL: "data_pipeline_hourly", "incremental_load"
   - Monitoring: "system_health_check", "error_rate_tracker"
   - Reporting: "executive_dashboard", "monthly_metrics"

3. For each scheduled query to generate:
   a. Select purpose category
   
   b. Generate CRON schedule based on category:
      - Analytics: Hourly, daily, or weekly
      - ETL: Every 5-30 minutes (often too frequent)
      - Monitoring: Every 1-15 minutes (often too frequent)
      - Reporting: Daily or weekly
   
   c. Assign cost per run based on frequency:
      - High frequency (< 15 min): $0.10 - $0.50 per run
      - Medium frequency (hourly): $0.50 - $2.00 per run
      - Low frequency (daily+): $2.00 - $10.00 per run
   
   d. Calculate daily cost:
      - daily_cost = cost_per_run × runs_per_day
   
   e. Add metadata:
      - data_scanned_mb: 100 MB - 50 GB per run
      - execution_time_sec: 5 - 300 seconds
      - last_modified: Random date in past 6 months
   
   f. Identify optimization opportunities:
      - 40% over-frequent (can reduce frequency)
      - 30% redundant (similar to other queries)
      - 20% materialized view candidates
      - 10% already optimized

4. Return list of scheduled query dictionaries
```


**Example Output**:

```python
[
    {
        "name": "user_activity_summary",
        "cron": "*/5 * * * *",  # Every 5 minutes - TOO FREQUENT
        "frequency": "every_5_minutes",
        "cost_per_run": 0.25,
        "daily_cost": 72.00,  # 288 runs/day × $0.25
        "data_scanned_mb": 5000,
        "execution_time_sec": 45,
        "purpose": "analytics",
        "optimization_opportunity": "reduce_frequency"
    },
    {
        "name": "sales_by_region",
        "cron": "0 * * * *",  # Every hour
        "frequency": "hourly",
        "cost_per_run": 1.50,
        "daily_cost": 36.00,  # 24 runs/day × $1.50
        "data_scanned_mb": 15000,
        "execution_time_sec": 120,
        "purpose": "analytics",
        "optimization_opportunity": "merge_with_similar"
    },
    {
        "name": "sales_by_country",
        "cron": "0 * * * *",  # Every hour - REDUNDANT
        "frequency": "hourly",
        "cost_per_run": 1.50,
        "daily_cost": 36.00,
        "data_scanned_mb": 15000,  # Same data as sales_by_region
        "execution_time_sec": 120,
        "purpose": "analytics",
        "optimization_opportunity": "merge_with_similar"
    },
    {
        "name": "daily_aggregates",
        "cron": "0 2 * * *",  # Daily at 2 AM
        "frequency": "daily",
        "cost_per_run": 8.00,
        "daily_cost": 8.00,
        "data_scanned_mb": 80000,
        "execution_time_sec": 300,
        "purpose": "reporting",
        "optimization_opportunity": "materialized_view"
    }
]
```

**Key Features**:
- Realistic CRON expressions for various frequencies
- Cost calculations based on frequency and data volume
- Intentional over-scheduling to demonstrate savings
- Metadata for identifying merge and materialization opportunities

### 4. ML Job Simulator

**Purpose**: Generate ML training job metadata with various accelerator types and configurations.

**Logic Flow**:

```
1. Input: Count (default 10)
2. Define job types:
   - Vision: "image_classification", "object_detection", "segmentation"
   - NLP: "language_model", "text_classification", "translation"
   - Recommendation: "collaborative_filtering", "ranking_model"
   - Forecasting: "time_series_prediction", "demand_forecasting"

3. For each ML job to generate:
   a. Select job type
   
   b. Assign accelerator type based on job:
      - Vision (large): A100 or V100 (expensive)
      - Vision (small): T4 (cost-effective)
      - NLP (large): A100 or TPU
      - NLP (small): V100 or T4
      - Recommendation: T4 or CPU
      - Forecasting: CPU or T4
   
   c. Generate resource configuration:
      - num_accelerators: 1, 2, 4, or 8
      - machine_type: n1-standard-4, n1-highmem-8, n1-highmem-16
      - training_duration_hours: 4 - 120 hours
   
   d. Calculate costs:
      - accelerator_cost = num_accelerators × price_per_hour × duration
      - cpu_cost = machine_price_per_hour × duration
      - total_cost = accelerator_cost + cpu_cost
   
   e. Assign VM type (intentionally suboptimal):
      - 80% on-demand (should use spot)
      - 20% spot
   
   f. Add utilization metrics:
      - gpu_utilization: 40% - 95% (lower = data loading issues)
      - peak_nodes: 1 - 20 (for distributed training)
      - avg_nodes: 50% - 100% of peak (lower = autoscaling opportunity)
   
   g. Identify optimization opportunities:
      - 80% can use spot VMs
      - 40% over-provisioned (wrong machine type)
      - 30% need autoscaling
      - 20% wrong accelerator type

4. Return list of ML job dictionaries
```


**Example Output**:

```python
[
    {
        "job_name": "image_classification_resnet50",
        "job_type": "vision",
        "accelerator_type": "V100",
        "num_accelerators": 4,
        "machine_type": "n1-highmem-16",
        "vm_type": "on-demand",  # Should use spot
        "training_duration_hours": 48,
        "gpu_utilization": 65,  # Could be higher with better data loading
        "peak_nodes": 4,
        "avg_nodes": 4,  # No autoscaling
        "accelerator_cost": 475.20,  # 4 × $2.48 × 48
        "cpu_cost": 45.12,  # $0.94 × 48
        "total_cost": 520.32,
        "optimization_opportunities": ["spot_vm", "data_pipeline"]
    },
    {
        "job_name": "small_text_classifier",
        "job_type": "nlp",
        "accelerator_type": "A100",  # Overkill for small model
        "num_accelerators": 2,
        "machine_type": "n1-highmem-32",  # Over-provisioned
        "vm_type": "on-demand",
        "training_duration_hours": 12,
        "gpu_utilization": 45,  # Low utilization
        "peak_nodes": 2,
        "avg_nodes": 2,
        "accelerator_cost": 88.08,  # 2 × $3.67 × 12
        "cpu_cost": 22.56,  # $1.88 × 12
        "total_cost": 110.64,
        "optimization_opportunities": ["spot_vm", "downgrade_accelerator", "right_size_machine"]
    },
    {
        "job_name": "distributed_recommendation_training",
        "job_type": "recommendation",
        "accelerator_type": "T4",
        "num_accelerators": 8,
        "machine_type": "n1-standard-8",
        "vm_type": "on-demand",
        "training_duration_hours": 72,
        "gpu_utilization": 85,  # Good utilization
        "peak_nodes": 8,
        "avg_nodes": 3,  # Autoscaling opportunity
        "accelerator_cost": 201.60,  # 8 × $0.35 × 72
        "cpu_cost": 54.72,  # $0.76 × 72
        "total_cost": 256.32,
        "optimization_opportunities": ["spot_vm", "autoscaling"]
    },
    {
        "job_name": "time_series_forecasting",
        "job_type": "forecasting",
        "accelerator_type": "none",  # CPU only
        "num_accelerators": 0,
        "machine_type": "n1-highmem-16",
        "vm_type": "on-demand",
        "training_duration_hours": 24,
        "gpu_utilization": 0,
        "peak_nodes": 1,
        "avg_nodes": 1,
        "accelerator_cost": 0,
        "cpu_cost": 22.56,  # $0.94 × 24
        "total_cost": 22.56,
        "optimization_opportunities": ["spot_vm"]
    }
]
```

**Key Features**:
- Realistic accelerator types and configurations for different ML workloads
- Intentional inefficiencies (on-demand VMs, over-provisioning, wrong accelerators)
- Utilization metrics to identify data loading and autoscaling issues
- Cost calculations based on actual GCP pricing
- Multiple optimization opportunities per job


### Simulator Design Principles

All simulators follow these key principles:

1. **Realism**: Generate data that closely mimics real-world scenarios with authentic patterns and distributions

2. **Intentional Inefficiency**: Create suboptimal configurations (70-80% of generated items) to demonstrate clear optimization opportunities

3. **Variety**: Include diverse scenarios across different scales, types, and use cases

4. **Measurability**: Generate sufficient metadata for accurate cost calculations and savings projections

5. **AI-Friendly**: Structure data in formats that AI models can easily analyze and provide recommendations for

6. **Reproducibility**: Use consistent patterns so users can understand the logic behind generated data

### Simulator Validation

Each simulator output is validated to ensure:

- **Data Completeness**: All required fields are present
- **Value Ranges**: Numeric values fall within realistic bounds
- **Consistency**: Related fields are logically consistent (e.g., cost matches duration × rate)
- **Optimization Potential**: At least 60% of generated items have clear optimization opportunities
- **Cost Accuracy**: Calculated costs match GCP pricing models

---

## Summary

This optimization guide demonstrates how the GCP Cost Optimization Dashboard identifies and resolves common cost waste scenarios across four key areas:

1. **SQL Query Optimization**: Reduces BigQuery costs by 50-80% through query pattern improvements
2. **Storage Optimization**: Reduces GCS costs by 40-70% through storage class optimization and lifecycle policies
3. **Query Scheduling Optimization**: Reduces scheduled query costs by 40-70% through frequency adjustments and query merging
4. **ML Auto Scaling Optimization**: Reduces ML training costs by 50-80% through spot VMs and resource right-sizing

The simulators generate realistic synthetic data that allows users to explore these optimizations without connecting to real enterprise systems, making the dashboard an effective educational and demonstration tool for GCP cost management best practices.

