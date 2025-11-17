# GCP Cost Optimization Dashboard

A Streamlit-based simulation dashboard that demonstrates Google Cloud Platform cost optimization strategies using AI-powered insights. This application simulates various GCP workloads and provides actionable optimization recommendations without requiring access to real enterprise data.

## Features

### 🔍 SQL Query Optimization (Baseline Benchmark)
- Simulates unoptimized BigQuery queries using public datasets
- AI-powered query optimization with specific improvements
- Real-time cost estimation using BigQuery dry-run API
- Visual comparison of before/after query costs
- Detailed breakdown of optimization techniques applied

### 💾 Storage Optimization
- Simulates GCS bucket scenarios with realistic metadata
- AI-driven storage class recommendations
- Identifies deletion candidates and compression opportunities
- Lifecycle policy suggestions
- Cost savings visualization per bucket

### ⏰ Query Scheduling Optimization
- Simulates BigQuery scheduled query patterns
- Identifies redundant and over-frequent queries
- Suggests query merging and materialized view opportunities
- Timeline visualization of query costs
- Frequency adjustment recommendations

### 🤖 ML Training Job Optimization
- Simulates ML training workloads on GCP
- Spot VM and machine type recommendations
- Autoscaling configuration suggestions
- Accelerator type optimization (GPU/TPU)
- Cost breakdown visualization

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account (for BigQuery public dataset access)
- AI API key (Google Gemini or OpenAI)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd gcp-cost-optimization-dashboard
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Up Environment Variables

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials (see Configuration section below).

## Configuration

### GCP Configuration

1. **Create a GCP Project** (if you don't have one):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Note your Project ID

2. **Enable BigQuery API**:
   - Navigate to APIs & Services > Library
   - Search for "BigQuery API"
   - Click Enable

3. **Create Service Account** (Optional - for authentication):
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Grant "BigQuery User" role
   - Create and download JSON key
   - Save the key file securely

4. **Update .env file**:
   ```
   GCP_PROJECT_ID=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
   ```

   **Note**: If you don't provide credentials, the app will use your default gcloud authentication.

### AI API Configuration

Choose one of the following AI providers:

#### Option 1: Google Gemini (Recommended)

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Update .env:
   ```
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your-gemini-api-key
   ```

#### Option 2: OpenAI

1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Update .env:
   ```
   AI_PROVIDER=openai
   OPENAI_API_KEY=your-openai-api-key
   ```

## Usage

### Running the Application

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.

### Module Usage Instructions

#### 1. SQL Query Optimization Module

1. Select "Baseline Benchmark" from the sidebar
2. Choose a public dataset from the dropdown (e.g., NYC Citibike, Natality)
3. Click "Simulate SQL Optimization"
4. Wait for the simulation to complete (generates queries, optimizes them, and runs dry-runs)
5. Review the results:
   - Comparison table showing before/after bytes processed
   - Bar chart comparing query costs
   - Pie chart showing total savings distribution
   - Before/after SQL text for each query

**What to expect**: 
- 5-10 unoptimized queries will be generated
- AI will optimize each query (add filters, specific columns, partition pruning)
- BigQuery dry-run will estimate costs for both versions
- Typical savings: 30-90% reduction in bytes processed

#### 2. Storage Optimization Module

1. Select "Storage Optimization" from the sidebar
2. Click "Simulate Storage Analysis"
3. Wait for the AI analysis to complete
4. Review the results:
   - Table showing bucket issues and recommendations
   - Pie chart of bucket size distribution
   - Bar chart of potential savings per bucket

**What to expect**:
- 10 synthetic GCS buckets with realistic metadata
- AI suggestions for storage class changes, deletions, compression
- Estimated savings percentages for each recommendation

#### 3. Query Scheduling Optimization Module

1. Select "Query Scheduling Optimization" from the sidebar
2. Click "Simulate Schedule Analysis"
3. Wait for the AI analysis to complete
4. Review the results:
   - Timeline/heatmap showing cost distribution over time
   - Comparison table with before/after schedules
   - Recommendations for frequency adjustments and merges

**What to expect**:
- 10 scheduled queries with various CRON patterns
- AI identification of redundant or over-frequent queries
- Suggestions for materialized views and query merging

#### 4. ML Training Job Optimization Module

1. Select "ML Auto Scaling Optimization" from the sidebar
2. Click "Simulate ML Job Analysis"
3. Wait for the AI analysis to complete
4. Review the results:
   - Donut chart showing cost breakdown by job
   - Table with optimization recommendations
   - Projected savings for each suggestion

**What to expect**:
- 10 ML training jobs with different accelerator types
- AI suggestions for spot VMs, machine type changes, autoscaling
- Typical savings: 40-70% through spot VM usage

## Troubleshooting

### Common Issues

#### 1. BigQuery Authentication Errors

**Error**: `Permission denied` or `Authentication failed`

**Solutions**:
- Ensure your GCP project has BigQuery API enabled
- Verify your service account has "BigQuery User" role
- Check that `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Try using default gcloud authentication: `gcloud auth application-default login`

#### 2. AI API Errors

**Error**: `Invalid API key` or `Rate limit exceeded`

**Solutions**:
- Verify your API key is correct in `.env`
- Check that you've selected the correct `AI_PROVIDER` (gemini or openai)
- For rate limits, wait a few minutes and try again
- Consider upgrading your AI API plan for higher quotas

#### 3. Module Not Loading

**Error**: Module shows blank or errors on load

**Solutions**:
- Check browser console for JavaScript errors
- Refresh the page (Ctrl+R or Cmd+R)
- Clear Streamlit cache: Click "Clear cache" in the hamburger menu
- Restart the Streamlit server

#### 4. Dry-Run Query Failures

**Error**: `Table not found` or `Syntax error`

**Solutions**:
- Ensure you have internet connectivity (public datasets require network access)
- Try a different public dataset from the dropdown
- Check that the BigQuery API is enabled in your GCP project
- Verify your project has access to BigQuery public datasets

#### 5. Slow Performance

**Issue**: Simulations take a long time to complete

**Solutions**:
- AI API calls can take 5-10 seconds per query
- BigQuery dry-runs are usually fast (<1 second)
- For SQL optimization with 10 queries, expect 1-2 minutes total
- Consider reducing the number of simulated items in the code

#### 6. Import Errors

**Error**: `ModuleNotFoundError` or `ImportError`

**Solutions**:
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)
- Try creating a fresh virtual environment:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt
  ```

### Debug Mode

To enable verbose logging for troubleshooting:

1. Set environment variable:
   ```bash
   export STREAMLIT_LOGGER_LEVEL=debug
   ```

2. Run the app:
   ```bash
   streamlit run app.py
   ```

3. Check the terminal output for detailed error messages

### Getting Help

If you encounter issues not covered here:

1. Check the [Streamlit documentation](https://docs.streamlit.io/)
2. Review [BigQuery API documentation](https://cloud.google.com/bigquery/docs)
3. Consult [Google Gemini API docs](https://ai.google.dev/docs) or [OpenAI API docs](https://platform.openai.com/docs)
4. Open an issue in the project repository with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python version)

## Architecture

The application follows a modular architecture:

```
├── app.py                          # Main Streamlit entry point
├── config.py                       # Configuration and constants
├── models/                         # Data models
│   └── data_models.py
├── services/                       # Core services
│   ├── ai_optimizer_service.py    # AI integration
│   ├── bigquery_service.py        # BigQuery integration
│   └── visualization_manager.py   # Chart generation
├── modules/                        # UI modules
│   ├── sql_optimization.py
│   ├── storage_optimization.py
│   ├── query_scheduling.py
│   └── ml_autoscaling.py
└── simulators/                     # Data simulators
    ├── sql_query_simulator.py
    ├── storage_simulator.py
    ├── schedule_simulator.py
    └── ml_job_simulator.py
```

## Cost Information

### BigQuery Costs

- **Dry-run queries**: FREE (no data is actually processed)
- **Public datasets**: FREE to query (Google provides free access)
- **Pricing formula**: $5 per TB of data processed (for reference only)

### AI API Costs

- **Google Gemini**: Free tier available, then pay-per-token
- **OpenAI**: Pay-per-token pricing
- **Typical usage**: 10-20 API calls per simulation
- **Estimated cost**: $0.01-0.10 per simulation session


## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Uses [Google BigQuery](https://cloud.google.com/bigquery) public datasets
- Powered by [Google Gemini](https://ai.google.dev/) or [OpenAI](https://openai.com/) AI
