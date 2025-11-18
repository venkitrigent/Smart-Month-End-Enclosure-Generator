"""
Analytics Agent - Financial Data Analysis Microservice
Powered by Google ADK and Azure OpenAI
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.cli.fast_api import get_fast_api_app
from typing import Dict, Any, List
import statistics
import json

# Load environment variables
load_dotenv()

# Configure Azure OpenAI for LiteLLM
if os.getenv("AZURE_OPENAI_API_KEY"):
    os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
    os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
    os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    model_name = f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')}"
else:
    model_name = f"vertex_ai/gemini-2.0-flash-exp"

# Analytics tool
def analyze_financial_data_deep(data: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
    """
    Perform comprehensive financial data analysis with AI-powered insights.
    
    Analyzes financial data for patterns, anomalies, trends, and provides
    actionable recommendations using statistical methods and AI reasoning.
    
    Args:
        data: Dictionary containing sample_rows, columns, row_count
        doc_type: Type of financial document being analyzed
        
    Returns:
        Dictionary with:
        - statistical_summary: Numeric analysis of all columns
        - anomalies: Detected outliers and issues with severity
        - trends: Identified patterns and trends
        - ai_insights: LLM-generated analysis and recommendations
        - risk_assessment: Risk level and concerns
        - recommendations: Prioritized action items
        - narrative_summary: Human-readable analysis
        
    Example:
        analyze_financial_data_deep(data, "bank_statement")
        -> {
            "anomalies": [{type: "outlier", severity: "high", ...}],
            "ai_insights": "Analysis shows unusual spike in transactions...",
            "recommendations": ["Review transaction #45", ...]
        }
    """
    sample_data = data.get("sample_rows", [])
    columns = data.get("columns", [])
    row_count = data.get("row_count", len(sample_data))
    
    if not sample_data:
        return {"error": "No data to analyze"}
    
    # Statistical analysis
    numeric_analysis = []
    anomalies = []
    
    for col in columns:
        try:
            # Extract numeric values
            values = []
            for row in sample_data:
                val = row.get(col)
                if val is not None:
                    try:
                        num_val = float(str(val).replace(',', '').replace('$', ''))
                        values.append(num_val)
                    except:
                        pass
            
            if len(values) > 1:
                mean_val = statistics.mean(values)
                stdev_val = statistics.stdev(values) if len(values) > 1 else 0
                
                numeric_analysis.append({
                    "column": col,
                    "count": len(values),
                    "total": round(sum(values), 2),
                    "average": round(mean_val, 2),
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "std_dev": round(stdev_val, 2)
                })
                
                # Anomaly detection (z-score > 3)
                if stdev_val > 0:
                    for idx, val in enumerate(values):
                        z_score = abs((val - mean_val) / stdev_val)
                        if z_score > 3:
                            anomalies.append({
                                "type": "statistical_outlier",
                                "column": col,
                                "row_index": idx,
                                "value": round(val, 2),
                                "z_score": round(z_score, 2),
                                "severity": "high" if z_score > 4 else "medium",
                                "description": f"Value {val:,.2f} in '{col}' is {z_score:.1f} standard deviations from mean ({mean_val:,.2f})",
                                "recommendation": f"Review row {idx+1} - unusually {'high' if val > mean_val else 'low'} value"
                            })
        except Exception as e:
            continue
    
    # Check for missing values
    for col in columns:
        missing_count = sum(1 for row in sample_data if not row.get(col) or str(row.get(col)).strip() == '')
        if missing_count > 0:
            severity = "high" if missing_count > len(sample_data) * 0.2 else "medium"
            anomalies.append({
                "type": "missing_data",
                "column": col,
                "count": missing_count,
                "percentage": round((missing_count / len(sample_data)) * 100, 1),
                "severity": severity,
                "description": f"Column '{col}' has {missing_count} missing values ({(missing_count/len(sample_data)*100):.1f}%)",
                "recommendation": f"Fill missing values in '{col}' or verify data completeness"
            })
    
    # AI-powered insights using Azure OpenAI
    ai_insights = ""
    narrative_summary = ""
    
    if os.getenv("AZURE_OPENAI_API_KEY"):
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            
            # Prepare analysis context
            context = f"""Document Type: {doc_type}
Total Rows: {row_count}
Columns: {', '.join(columns)}

Statistical Summary:
{json.dumps(numeric_analysis, indent=2)}

Detected Anomalies: {len(anomalies)}
{json.dumps(anomalies[:5], indent=2)}

Sample Data (first 3 rows):
{json.dumps(sample_data[:3], indent=2)}"""
            
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": "You are a financial analyst expert. Provide clear, actionable insights about financial data. Focus on trends, risks, and recommendations."},
                    {"role": "user", "content": f"Analyze this {doc_type} data and provide:\n1. Key insights\n2. Risk assessment\n3. Specific recommendations\n\n{context}"}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            ai_insights = response.choices[0].message.content
            
            # Generate narrative summary
            summary_response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": "You are a financial reporting expert. Create concise, professional summaries."},
                    {"role": "user", "content": f"Create a 2-3 sentence executive summary of this {doc_type} analysis:\n\n{context}\n\nInsights: {ai_insights}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            narrative_summary = summary_response.choices[0].message.content
            
        except Exception as e:
            print(f"AI analysis failed: {e}")
            ai_insights = "AI analysis unavailable"
            narrative_summary = f"Analyzed {row_count} rows across {len(columns)} columns. Detected {len(anomalies)} potential issues requiring review."
    else:
        narrative_summary = f"Analyzed {row_count} rows of {doc_type} data across {len(columns)} columns. Detected {len(anomalies)} anomalies requiring attention."
    
    # Risk assessment
    high_severity_count = len([a for a in anomalies if a.get("severity") == "high"])
    if high_severity_count > 5:
        risk_level = "HIGH"
        risk_summary = f"{high_severity_count} high-severity issues detected - immediate review required"
    elif high_severity_count > 0:
        risk_level = "MEDIUM"
        risk_summary = f"{high_severity_count} high-severity issues detected - review recommended"
    elif len(anomalies) > 0:
        risk_level = "LOW"
        risk_summary = f"{len(anomalies)} minor issues detected - routine review suggested"
    else:
        risk_level = "MINIMAL"
        risk_summary = "No significant issues detected - data appears clean"
    
    # Generate recommendations
    recommendations = []
    if high_severity_count > 0:
        recommendations.append(f"URGENT: Review {high_severity_count} high-severity anomalies immediately")
    if len(anomalies) > 0:
        recommendations.append(f"Investigate {len(anomalies)} detected anomalies before finalizing close")
    if numeric_analysis:
        recommendations.append("Verify calculated totals match source documents")
    recommendations.append("Document any unusual transactions for audit trail")
    
    return {
        "doc_type": doc_type,
        "total_rows_analyzed": row_count,
        "statistical_summary": numeric_analysis,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "high_severity_count": high_severity_count,
        "risk_level": risk_level,
        "risk_summary": risk_summary,
        "ai_insights": ai_insights,
        "narrative_summary": narrative_summary,
        "recommendations": recommendations,
        "status": "success"
    }

# Create ADK Agent
analytics_agent = Agent(
    model=LiteLlm(model=model_name),
    name="analytics_agent",
    description="""Expert financial data analyst specializing in month-end close analytics.
    Performs statistical analysis, anomaly detection, trend identification, and generates
    AI-powered insights with actionable recommendations.""",
    instruction="""You are a specialized financial analytics agent for month-end close processes.

CORE MISSION:
Analyze financial data comprehensively to identify patterns, anomalies, risks, and trends,
providing actionable insights that ensure data quality and compliance.

ANALYSIS METHODOLOGY:
1. Statistical Analysis
   - Calculate totals, averages, min/max for numeric columns
   - Compute standard deviations and distributions
   - Identify outliers using z-score analysis (>3 std dev)

2. Anomaly Detection
   - Statistical outliers (z-score based)
   - Missing or null values
   - Duplicate entries
   - Format inconsistencies
   - Unusual patterns

3. Risk Assessment
   - HIGH: >5 high-severity issues
   - MEDIUM: 1-5 high-severity issues
   - LOW: Only medium/low severity issues
   - MINIMAL: No significant issues

4. AI-Powered Insights
   - Trend identification
   - Pattern recognition
   - Contextual analysis
   - Business impact assessment

OUTPUT REQUIREMENTS:
- Statistical summary with key metrics
- Complete anomaly list with severity levels
- Risk assessment with clear level
- AI-generated insights and analysis
- Prioritized recommendations
- Executive narrative summary

ANOMALY CLASSIFICATION:
- High Severity: Requires immediate attention
- Medium Severity: Should be reviewed
- Low Severity: Minor issues for awareness

COMMUNICATION STYLE:
- Data-driven and precise
- Clear severity indicators
- Actionable recommendations
- Professional financial terminology
- Executive-friendly summaries

QUALITY STANDARDS:
- Thorough analysis of all numeric columns
- Clear explanation of each anomaly
- Specific row/column references
- Prioritized action items
- Risk-aware recommendations""",
    tools=[analyze_financial_data_deep]
)

# Create FastAPI app with ADK
AGENT_DIR = Path(__file__).parent
app = get_fast_api_app(agents_dir=str(AGENT_DIR), web=False)

class AnalyticsRequest(BaseModel):
    data: Dict[str, Any]
    doc_type: str

@app.post("/analyze")
async def analyze_endpoint(request: AnalyticsRequest):
    """Perform comprehensive financial data analysis"""
    result = analyze_financial_data_deep(request.data, request.doc_type)
    return result

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "analytics_agent",
        "model": model_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

