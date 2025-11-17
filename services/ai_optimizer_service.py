"""
AI Optimizer Service for GCP Cost Optimization Dashboard

This service provides AI-powered optimization suggestions for:
- SQL queries
- Storage buckets
- Scheduled queries
- ML training jobs
"""

import json
import time
from typing import Dict, List, Optional
import streamlit as st
from config import Config


class AIErrorHandler:
    """Handles AI API errors with retry logic"""
    
    @staticmethod
    def handle_ai_error(error: Exception, retry_count: int = 3) -> Optional[Dict]:
        """
        Handles AI API errors with exponential backoff
        
        Args:
            error: The exception that occurred
            retry_count: Number of retries remaining
            
        Returns:
            Error information dictionary or None if retries exhausted
        """
        error_message = str(error)
        error_type = "unknown"
        user_message = error_message
        should_retry = False
        
        # Identify error type
        if "rate limit" in error_message.lower() or "quota" in error_message.lower():
            error_type = "rate_limit"
            user_message = "API rate limit exceeded. Retrying with exponential backoff..."
            should_retry = retry_count > 0
        elif "api key" in error_message.lower() or "authentication" in error_message.lower():
            error_type = "authentication"
            user_message = "Invalid API key or authentication failed"
            should_retry = False
        elif "timeout" in error_message.lower():
            error_type = "timeout"
            user_message = "Request timed out. Retrying..."
            should_retry = retry_count > 0
        elif "json" in error_message.lower() or "parse" in error_message.lower():
            error_type = "invalid_response"
            user_message = "Failed to parse AI response. The response format was invalid."
            should_retry = False
        
        return {
            "error_type": error_type,
            "user_message": user_message,
            "should_retry": should_retry,
            "original_error": error_message
        }


class AIOptimizerService:
    """Service for AI-powered cost optimization suggestions"""
    
    def __init__(self, api_key: str, provider: str = "gemini"):
        """
        Initialize AI optimizer with API credentials
        
        Args:
            api_key: API key for AI service
            provider: "gemini" or "openai"
        """
        self.api_key = api_key
        self.provider = provider.lower()
        self.client = None
        
        if self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('models/gemini-2.5-flash')
        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}. Use 'gemini' or 'openai'")
    
    def _call_ai_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call AI API with exponential backoff retry logic
        
        Args:
            prompt: The prompt to send to the AI
            max_retries: Maximum number of retry attempts
            
        Returns:
            AI response text
            
        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                if self.provider == "gemini":
                    response = self.client.generate_content(prompt)
                    return response.text
                elif self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a GCP cost optimization expert."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3
                    )
                    return response.choices[0].message.content
            except Exception as e:
                error_info = AIErrorHandler.handle_ai_error(e, max_retries - attempt - 1)
                
                if not error_info["should_retry"] or attempt == max_retries - 1:
                    raise Exception(f"{error_info['user_message']}: {error_info['original_error']}")
                
                # Exponential backoff: 2^attempt seconds
                wait_time = 2 ** attempt
                time.sleep(wait_time)
        
        raise Exception("Failed to get AI response after all retries")
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON from AI response, handling markdown code blocks
        
        Args:
            response_text: Raw AI response text
            
        Returns:
            Parsed JSON dictionary
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {e}. Response: {text[:200]}")

    
    @st.cache_data(ttl=3600, show_spinner=False)
    def optimize_sql_query(_self, query: str, dataset_info: Dict) -> Dict:
        """
        Optimizes a SQL query using AI.
        Cached for 1 hour to improve performance and reduce API calls.
        
        Args:
            query: Original SQL query
            dataset_info: Information about the dataset schema
            
        Returns:
            {
                "optimized_query": str,
                "optimizations_applied": List[str],
                "explanation": str
            }
        """
        prompt = f"""You are a BigQuery optimization expert. Analyze this SQL query and optimize it for cost reduction.

Original Query:
{query}

Dataset: {dataset_info.get('dataset', 'N/A')}
Table: {dataset_info.get('table', 'N/A')}

Apply these optimizations where applicable:
1. Replace SELECT * with specific columns (use common column names like id, name, date, timestamp, user_id, etc.)
2. Add WHERE clauses to filter data and reduce data scanned
3. Add partition filters if the table has date/timestamp partitions (use _PARTITIONTIME or date columns)
4. Remove unnecessary JOINs or replace with more efficient alternatives
5. Simplify complex subqueries
6. Add LIMIT clauses where appropriate

Return ONLY a valid JSON response with this exact structure (no markdown, no code blocks):
{{
    "optimized_query": "the improved SQL query as a string",
    "optimizations_applied": ["list of specific changes made"],
    "explanation": "brief explanation of improvements and expected cost impact"
}}"""
        
        try:
            response_text = _self._call_ai_with_retry(prompt)
            result = _self._parse_json_response(response_text)
            
            # Validate response structure
            required_keys = ["optimized_query", "optimizations_applied", "explanation"]
            for key in required_keys:
                if key not in result:
                    raise Exception(f"Missing required key in AI response: {key}")
            
            return result
        except Exception as e:
            raise Exception(f"Failed to optimize SQL query: {str(e)}")

    
    @st.cache_data(ttl=3600, show_spinner=False)
    def analyze_storage(_self, buckets: List[Dict]) -> List[Dict]:
        """
        Analyzes storage buckets and suggests optimizations.
        Cached for 1 hour to improve performance and reduce API calls.
        
        Args:
            buckets: List of bucket metadata dictionaries
            
        Returns:
            List of optimization suggestions with:
            - bucket_name: str
            - issue: str
            - suggestion: str
            - estimated_savings_percent: float
        """
        buckets_json = json.dumps(buckets, indent=2, default=str)
        
        prompt = f"""You are a GCS storage optimization expert. Analyze these storage buckets and suggest cost optimizations.

Buckets:
{buckets_json}

For each bucket, identify optimization opportunities:
1. Storage class optimization (STANDARD → NEARLINE/COLDLINE/ARCHIVE for infrequently accessed data)
2. Deletion candidates (old, unused data that hasn't been accessed in months)
3. Compression opportunities (uncompressed files that could be compressed)
4. Lifecycle rule suggestions (automatic transitions or deletions)
5. Cross-region cost improvements (moving to cheaper regions)

Storage class costs per GB/month:
- STANDARD: $0.020
- NEARLINE: $0.010
- COLDLINE: $0.004
- ARCHIVE: $0.0012

Return ONLY a valid JSON array with this structure (no markdown, no code blocks):
[
    {{
        "bucket_name": "bucket name",
        "issue": "description of the issue",
        "suggestion": "specific actionable recommendation",
        "estimated_savings_percent": 25.5
    }}
]

Provide 3-5 optimization suggestions with realistic savings percentages."""
        
        try:
            response_text = _self._call_ai_with_retry(prompt)
            result = _self._parse_json_response(response_text)
            
            # Validate response is a list
            if not isinstance(result, list):
                raise Exception("AI response must be a list of optimization suggestions")
            
            # Validate each suggestion has required keys
            required_keys = ["bucket_name", "issue", "suggestion", "estimated_savings_percent"]
            for suggestion in result:
                for key in required_keys:
                    if key not in suggestion:
                        raise Exception(f"Missing required key in suggestion: {key}")
            
            return result
        except Exception as e:
            raise Exception(f"Failed to analyze storage: {str(e)}")

    
    @st.cache_data(ttl=3600, show_spinner=False)
    def optimize_schedule(_self, schedules: List[Dict]) -> Dict:
        """
        Analyzes scheduled queries and suggests optimizations.
        Cached for 1 hour to improve performance and reduce API calls.
        
        Args:
            schedules: List of scheduled query metadata
            
        Returns:
            {
                "redundant_queries": List[str],
                "frequency_adjustments": List[Dict],
                "merge_opportunities": List[Dict],
                "materialized_view_candidates": List[str],
                "estimated_savings": float
            }
        """
        schedules_json = json.dumps(schedules, indent=2, default=str)
        
        prompt = f"""You are a BigQuery scheduled query optimization expert. Analyze these scheduled queries and suggest optimizations.

Scheduled Queries:
{schedules_json}

Identify optimization opportunities:
1. Redundant schedules (queries that produce duplicate or overlapping results)
2. Over-frequent queries (queries running more often than necessary)
3. Merge-able jobs (queries that could be combined into a single query)
4. Materialized view candidates (frequently-run queries that could be materialized)

Return ONLY a valid JSON response with this exact structure (no markdown, no code blocks):
{{
    "redundant_queries": ["list of query names that are redundant"],
    "frequency_adjustments": [
        {{
            "query_name": "name",
            "current_frequency": "hourly",
            "suggested_frequency": "daily",
            "reasoning": "explanation"
        }}
    ],
    "merge_opportunities": [
        {{
            "queries": ["query1", "query2"],
            "reasoning": "why they can be merged"
        }}
    ],
    "materialized_view_candidates": ["list of query names that should be materialized views"],
    "estimated_savings": 35.5
}}

Provide realistic optimization suggestions with estimated total savings percentage."""
        
        try:
            response_text = _self._call_ai_with_retry(prompt)
            result = _self._parse_json_response(response_text)
            
            # Validate response structure
            required_keys = [
                "redundant_queries",
                "frequency_adjustments",
                "merge_opportunities",
                "materialized_view_candidates",
                "estimated_savings"
            ]
            for key in required_keys:
                if key not in result:
                    raise Exception(f"Missing required key in AI response: {key}")
            
            return result
        except Exception as e:
            raise Exception(f"Failed to optimize schedules: {str(e)}")

    
    @st.cache_data(ttl=3600, show_spinner=False)
    def optimize_ml_jobs(_self, jobs: List[Dict]) -> List[Dict]:
        """
        Analyzes ML jobs and suggests compute optimizations.
        Cached for 1 hour to improve performance and reduce API calls.
        
        Args:
            jobs: List of ML training job metadata
            
        Returns:
            List of optimization suggestions with:
            - job_name: str
            - current_config: Dict
            - suggested_config: Dict
            - optimization_type: str
            - estimated_savings_percent: float
        """
        jobs_json = json.dumps(jobs, indent=2, default=str)
        
        prompt = f"""You are a GCP ML compute optimization expert. Analyze these ML training jobs and suggest cost optimizations.

ML Training Jobs:
{jobs_json}

GPU/TPU hourly costs:
- T4: $0.35/hour
- V100: $2.48/hour
- A100: $3.67/hour
- TPU_V2: $4.50/hour
- TPU_V3: $8.00/hour

Spot VMs provide ~70% discount on average.

Identify optimization opportunities:
1. Spot VM usage (use preemptible instances for fault-tolerant workloads)
2. Machine type reduction (downgrade to smaller accelerators if possible)
3. Autoscaling adjustments (reduce peak nodes, enable autoscaling)
4. Vertex AI caching (cache preprocessing steps)
5. Accelerator alternatives (switch to cheaper but sufficient accelerators)

Return ONLY a valid JSON array with this structure (no markdown, no code blocks):
[
    {{
        "job_name": "job name",
        "current_config": {{
            "accelerator_type": "A100",
            "gpu_hours": 100,
            "spot_vm": false
        }},
        "suggested_config": {{
            "accelerator_type": "T4",
            "gpu_hours": 100,
            "spot_vm": true
        }},
        "optimization_type": "spot_vm_and_downgrade",
        "estimated_savings_percent": 85.5
    }}
]

Provide 3-5 optimization suggestions with realistic savings percentages."""
        
        try:
            response_text = _self._call_ai_with_retry(prompt)
            result = _self._parse_json_response(response_text)
            
            # Validate response is a list
            if not isinstance(result, list):
                raise Exception("AI response must be a list of optimization suggestions")
            
            # Validate each suggestion has required keys
            required_keys = [
                "job_name",
                "current_config",
                "suggested_config",
                "optimization_type",
                "estimated_savings_percent"
            ]
            for suggestion in result:
                for key in required_keys:
                    if key not in suggestion:
                        raise Exception(f"Missing required key in suggestion: {key}")
            
            return result
        except Exception as e:
            raise Exception(f"Failed to optimize ML jobs: {str(e)}")
