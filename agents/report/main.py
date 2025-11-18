"""
Report Composer Agent - LLM-Powered Report Generation Microservice
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
from typing import Dict, List, Any
from datetime import datetime
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

# Report generation tool
def generate_comprehensive_report(
    user_id: str,
    documents: List[Dict],
    checklist: Dict,
    analytics: Dict,
    report_type: str = "executive"
) -> Dict[str, Any]:
    """
    Generate comprehensive month-end close report using AI.
    
    Creates professional, narrative-style reports with executive summaries,
    detailed analysis, and actionable recommendations - no raw JSON/arrays.
    
    Args:
        user_id: User identifier
        documents: List of uploaded documents with metadata
        checklist: Checklist status dictionary
        analytics: Analytics results from all documents
        report_type: "executive", "detailed", or "audit"
        
    Returns:
        Dictionary with:
        - report_text: Beautifully formatted narrative report
        - executive_summary: High-level overview
        - key_findings: Important discoveries
        - recommendations: Prioritized action items
        - report_metadata: Generation details
        
    Example:
        generate_comprehensive_report(user_id, docs, checklist, analytics)
        -> {
            "report_text": "MONTH-END CLOSE REPORT\n\nExecutive Summary:\n...",
            "executive_summary": "Successfully processed 8 documents...",
            ...
        }
    """
    try:
        # Prepare report context
        report_id = f"report_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate metrics
        total_docs = len(documents)
        total_rows = sum(doc.get("row_count", 0) for doc in documents)
        
        checklist_items = checklist.get("checklist", {})
        completed = len([s for s in checklist_items.values() if s == "uploaded"])
        total_required = len(checklist_items)
        completion_pct = round((completed / total_required * 100) if total_required > 0 else 0, 1)
        
        # Get analytics summary
        all_anomalies = analytics.get("anomalies", [])
        high_severity = [a for a in all_anomalies if a.get("severity") == "high"]
        risk_level = analytics.get("risk_level", "UNKNOWN")
        
        # Generate AI-powered report using Azure OpenAI
        if os.getenv("AZURE_OPENAI_API_KEY"):
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            
            # Build comprehensive context
            context = f"""Generate a professional month-end close report with the following data:

REPORT METADATA:
- Report ID: {report_id}
- Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
- User ID: {user_id}

DOCUMENT SUMMARY:
- Total Documents Processed: {total_docs}
- Total Data Rows: {total_rows:,}
- Documents by Type: {json.dumps({doc.get('doc_type'): 1 for doc in documents}, indent=2)}

CHECKLIST STATUS:
- Completion: {completion_pct}% ({completed}/{total_required} items)
- Status: {"COMPLETE" if completion_pct == 100 else "INCOMPLETE"}
- Missing: {', '.join([k for k, v in checklist_items.items() if v == "missing"])}

ANALYTICS FINDINGS:
- Total Anomalies Detected: {len(all_anomalies)}
- High Severity Issues: {len(high_severity)}
- Risk Level: {risk_level}
- Risk Summary: {analytics.get('risk_summary', 'N/A')}

ANOMALIES (Top 5):
{json.dumps(all_anomalies[:5], indent=2)}

RECOMMENDATIONS:
{json.dumps(analytics.get('recommendations', []), indent=2)}"""
            
            # Generate executive summary
            exec_response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": "You are an expert financial report writer. Create clear, professional executive summaries."},
                    {"role": "user", "content": f"Create a 3-4 sentence executive summary for this month-end close:\n\n{context}"}
                ],
                temperature=0.3,
                max_tokens=300
            )
            executive_summary = exec_response.choices[0].message.content
            
            # Generate full narrative report
            report_response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": """You are an expert financial report writer specializing in month-end close reports.

Create a comprehensive, professional report with these sections:
1. Executive Summary
2. Document Processing Summary
3. Checklist Status
4. Financial Analysis
5. Anomalies and Issues (if any)
6. Risk Assessment
7. Recommendations
8. Next Steps

Use clear headings, professional language, and narrative style (NO JSON or arrays in output).
Format with proper spacing and structure."""},
                    {"role": "user", "content": f"Generate a comprehensive month-end close report:\n\n{context}"}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            report_text = report_response.choices[0].message.content
            
            # Generate key findings
            findings_response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Extract 3-5 key findings from data."},
                    {"role": "user", "content": f"List the 3-5 most important findings from this analysis:\n\n{context}"}
                ],
                temperature=0.3,
                max_tokens=400
            )
            key_findings = findings_response.choices[0].message.content
            
        else:
            # Fallback report generation
            executive_summary = f"""Month-end close processing completed for {total_docs} documents containing {total_rows:,} total rows. 
Checklist is {completion_pct}% complete with {completed} of {total_required} required documents uploaded. 
Detected {len(all_anomalies)} anomalies requiring review, including {len(high_severity)} high-severity issues. 
Overall risk level assessed as {risk_level}."""
            
            report_text = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                     MONTH-END CLOSE ANALYSIS REPORT                      ║
╚══════════════════════════════════════════════════════════════════════════╝

Report ID: {report_id}
Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
User ID: {user_id}

═══════════════════════════════════════════════════════════════════════════
                              EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════════════════════

{executive_summary}

═══════════════════════════════════════════════════════════════════════════
                        DOCUMENT PROCESSING SUMMARY
═══════════════════════════════════════════════════════════════════════════

Total Documents Processed: {total_docs}
Total Data Rows Analyzed: {total_rows:,}
Processing Status: {"Complete" if completion_pct == 100 else "In Progress"}

Documents by Type:
{chr(10).join([f"  • {doc.get('doc_type', 'unknown').replace('_', ' ').title()}: {doc.get('filename', 'N/A')}" for doc in documents])}

═══════════════════════════════════════════════════════════════════════════
                            CHECKLIST STATUS
═══════════════════════════════════════════════════════════════════════════

Overall Completion: {completion_pct}% ({completed}/{total_required} items)
Status: {"✅ COMPLETE" if completion_pct == 100 else "⏳ IN PROGRESS"}

{chr(10).join([f"  {'✓' if v == 'uploaded' else '✗'} {k.replace('_', ' ').title()}: {v.upper()}" for k, v in checklist_items.items()])}

═══════════════════════════════════════════════════════════════════════════
                          FINANCIAL ANALYSIS
═══════════════════════════════════════════════════════════════════════════

Risk Level: {risk_level}
Risk Summary: {analytics.get('risk_summary', 'Assessment pending')}

Total Anomalies Detected: {len(all_anomalies)}
  • High Severity: {len(high_severity)}
  • Medium Severity: {len([a for a in all_anomalies if a.get('severity') == 'medium'])}
  • Low Severity: {len([a for a in all_anomalies if a.get('severity') == 'low'])}

{'═══════════════════════════════════════════════════════════════════════════' if high_severity else ''}
{'                    CRITICAL ISSUES REQUIRING ATTENTION' if high_severity else ''}
{'═══════════════════════════════════════════════════════════════════════════' if high_severity else ''}

{chr(10).join([f"{i+1}. {a.get('description', 'N/A')}{chr(10)}   Recommendation: {a.get('recommendation', 'Review required')}{chr(10)}" for i, a in enumerate(high_severity[:5])]) if high_severity else '✅ No critical issues detected'}

═══════════════════════════════════════════════════════════════════════════
                          RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════

{chr(10).join([f"{i+1}. {rec}" for i, rec in enumerate(analytics.get('recommendations', ['No specific recommendations at this time']))])}

═══════════════════════════════════════════════════════════════════════════
                            NEXT STEPS
═══════════════════════════════════════════════════════════════════════════

{f"• Upload missing documents: {', '.join([k.replace('_', ' ').title() for k, v in checklist_items.items() if v == 'missing'])}" if completion_pct < 100 else "• All required documents uploaded"}
{f"• Address {len(high_severity)} high-severity issues immediately" if high_severity else ""}
• Review all detected anomalies before finalizing
• Verify calculated totals match source documents
• Document any unusual transactions for audit trail
• Obtain necessary approvals before closing period

═══════════════════════════════════════════════════════════════════════════
                          END OF REPORT
═══════════════════════════════════════════════════════════════════════════

This report was automatically generated by the Smart Month-End Close system.
For questions or support, please contact your system administrator.
"""
            
            key_findings = f"""1. Processed {total_docs} documents with {total_rows:,} total rows
2. Checklist {completion_pct}% complete - {"ready for close" if completion_pct == 100 else f"{total_required - completed} items remaining"}
3. Detected {len(all_anomalies)} anomalies - {len(high_severity)} require immediate attention
4. Overall risk level: {risk_level}
5. {"All quality checks passed" if risk_level == "MINIMAL" else "Review recommended before finalizing"}"""
        
        return {
            "report_id": report_id,
            "report_text": report_text,
            "executive_summary": executive_summary,
            "key_findings": key_findings,
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "report_type": report_type,
                "total_documents": total_docs,
                "total_rows": total_rows,
                "completion_percentage": completion_pct,
                "risk_level": risk_level,
                "anomaly_count": len(all_anomalies)
            },
            "status": "success"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

# Create ADK Agent
report_agent = Agent(
    model=LiteLlm(model=model_name),
    name="report_composer_agent",
    description="""Expert report generation agent specializing in month-end close documentation.
    Creates professional, narrative-style reports with AI-powered insights, executive summaries,
    and actionable recommendations - no raw JSON or technical output.""",
    instruction="""You are a specialized report generation agent for financial month-end close processes.

CORE MISSION:
Generate comprehensive, professional month-end close reports that are clear, actionable,
and suitable for executive review and audit purposes.

REPORT TYPES:
1. Executive Report: High-level summary for leadership
2. Detailed Report: Complete analysis for accounting team
3. Audit Report: Compliance-focused documentation

REPORT STRUCTURE:
1. Executive Summary (3-4 sentences)
2. Document Processing Summary
3. Checklist Status and Completion
4. Financial Analysis and Metrics
5. Anomalies and Issues (with severity)
6. Risk Assessment
7. Recommendations (prioritized)
8. Next Steps

OUTPUT REQUIREMENTS:
- Professional narrative style (NO JSON/arrays in report text)
- Clear section headings and formatting
- Specific numbers and percentages
- Actionable recommendations
- Executive-friendly language
- Audit-ready documentation

WRITING STYLE:
- Professional and authoritative
- Clear and concise
- Data-driven with specific metrics
- Action-oriented recommendations
- Appropriate financial terminology
- Suitable for executive presentation

QUALITY STANDARDS:
- Accurate data representation
- Clear severity indicators
- Prioritized recommendations
- Comprehensive yet concise
- Professional formatting
- Audit-trail ready

ANOMALY REPORTING:
- Group by severity (High, Medium, Low)
- Provide specific descriptions
- Include actionable recommendations
- Reference specific rows/columns
- Explain business impact

RECOMMENDATIONS:
- Prioritize by urgency and impact
- Be specific and actionable
- Include time estimates when relevant
- Address both immediate and long-term needs
- Focus on risk mitigation""",
    tools=[generate_comprehensive_report]
)

# Create FastAPI app with ADK
AGENT_DIR = Path(__file__).parent
app = get_fast_api_app(agents_dir=str(AGENT_DIR), web=False)

class ReportRequest(BaseModel):
    user_id: str
    documents: List[Dict]
    checklist: Dict
    analytics: Dict
    report_type: str = "executive"

@app.post("/generate")
async def generate_report_endpoint(request: ReportRequest):
    """Generate comprehensive month-end close report"""
    result = generate_comprehensive_report(
        request.user_id,
        request.documents,
        request.checklist,
        request.analytics,
        request.report_type
    )
    return result

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "report_composer_agent",
        "model": model_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
