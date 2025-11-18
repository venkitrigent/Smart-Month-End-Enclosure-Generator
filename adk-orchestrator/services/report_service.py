"""
Report generation service for month-end close
"""

from typing import Dict, List, Any
from datetime import datetime
import json


class ReportService:
    """Generates month-end close reports"""
    
    def generate_summary_report(self, user_id: str, documents: List[Dict[str, Any]], 
                               checklist: Dict[str, str], analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive month-end close summary report"""
        
        report = {
            "report_id": f"report_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "summary": {
                "total_documents": len(documents),
                "documents_by_type": self._count_by_type(documents),
                "checklist_completion": self._calculate_completion(checklist),
                "status": self._determine_status(checklist)
            },
            "documents": documents,
            "checklist": checklist,
            "analytics": analytics,
            "recommendations": self._generate_recommendations(checklist, analytics)
        }
        
        return report
    
    def _count_by_type(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count documents by type"""
        counts = {}
        for doc in documents:
            doc_type = doc.get("doc_type", "unknown")
            counts[doc_type] = counts.get(doc_type, 0) + 1
        return counts
    
    def _calculate_completion(self, checklist: Dict[str, str]) -> Dict[str, Any]:
        """Calculate checklist completion percentage"""
        total = len(checklist)
        completed = len([s for s in checklist.values() if s == "uploaded"])
        
        return {
            "completed": completed,
            "total": total,
            "percentage": round((completed / total * 100) if total > 0 else 0, 1),
            "missing_count": total - completed
        }
    
    def _determine_status(self, checklist: Dict[str, str]) -> str:
        """Determine overall status"""
        completion = self._calculate_completion(checklist)
        
        if completion["percentage"] == 100:
            return "COMPLETE"
        elif completion["percentage"] >= 75:
            return "NEARLY_COMPLETE"
        elif completion["percentage"] >= 50:
            return "IN_PROGRESS"
        else:
            return "INCOMPLETE"
    
    def _generate_recommendations(self, checklist: Dict[str, str], 
                                  analytics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on data"""
        recommendations = []
        
        # Check for missing documents
        missing = [doc for doc, status in checklist.items() if status == "missing"]
        if missing:
            recommendations.append(f"Upload missing documents: {', '.join(missing)}")
        
        # Check for anomalies
        if analytics.get("anomalies_detected", 0) > 0:
            recommendations.append(f"Review {analytics['anomalies_detected']} detected anomalies")
        
        # Check data quality
        if analytics.get("total_rows", 0) == 0:
            recommendations.append("No data found in uploaded documents")
        
        if not recommendations:
            recommendations.append("All checks passed. Ready for month-end close.")
        
        return recommendations
    
    def generate_text_report(self, report_data: Dict[str, Any]) -> str:
        """Generate a human-readable text report"""
        
        summary = report_data["summary"]
        
        text = f"""
MONTH-END CLOSE REPORT
Generated: {report_data['generated_at']}
User ID: {report_data['user_id']}

=== SUMMARY ===
Status: {summary['status']}
Total Documents: {summary['total_documents']}
Checklist Completion: {summary['checklist_completion']['percentage']}%

=== DOCUMENTS BY TYPE ===
"""
        for doc_type, count in summary['documents_by_type'].items():
            text += f"  - {doc_type}: {count}\n"
        
        text += "\n=== CHECKLIST STATUS ===\n"
        for doc_type, status in report_data['checklist'].items():
            icon = "✓" if status == "uploaded" else "✗"
            text += f"  {icon} {doc_type}: {status}\n"
        
        text += "\n=== RECOMMENDATIONS ===\n"
        for i, rec in enumerate(report_data['recommendations'], 1):
            text += f"  {i}. {rec}\n"
        
        return text
    
    def generate_detailed_text_report(self, report_data: Dict[str, Any]) -> str:
        """Generate a comprehensive human-readable text report with deep analysis"""
        
        summary = report_data["summary"]
        analytics = report_data.get("analytics", {})
        
        text = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                     MONTH-END CLOSE ANALYSIS REPORT                      ║
╚══════════════════════════════════════════════════════════════════════════╝

Report ID: {report_data['report_id']}
Generated: {report_data['generated_at']}
User ID: {report_data['user_id']}

═══════════════════════════════════════════════════════════════════════════
                              EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════════════════════

Overall Status: {summary['status']}
Total Documents Processed: {summary['total_documents']}
Total Data Rows: {analytics.get('total_rows', 0):,}
Checklist Completion: {summary['checklist_completion']['percentage']}% ({summary['checklist_completion']['completed']}/{summary['checklist_completion']['total']} items)

"""
        
        # Financial Summary
        if 'financial_summary' in analytics:
            fin = analytics['financial_summary']
            text += f"""
═══════════════════════════════════════════════════════════════════════════
                            FINANCIAL SUMMARY
═══════════════════════════════════════════════════════════════════════════

Total Transaction Amount: ${fin.get('total_amount', 0):,.2f}
Number of Transactions: {fin.get('transaction_count', 0):,}
Average Transaction Value: ${fin.get('avg_amount', 0):,.2f}

"""
        
        # Documents by Type
        text += f"""
═══════════════════════════════════════════════════════════════════════════
                          DOCUMENTS BY TYPE
═══════════════════════════════════════════════════════════════════════════

"""
        for doc_type, count in summary['documents_by_type'].items():
            text += f"  • {doc_type.replace('_', ' ').title()}: {count} document(s)\n"
        
        # Checklist Status
        text += f"""

═══════════════════════════════════════════════════════════════════════════
                          CHECKLIST STATUS
═══════════════════════════════════════════════════════════════════════════

"""
        for doc_type, status in report_data['checklist'].items():
            icon = "✓" if status == "uploaded" else "✗"
            status_text = "UPLOADED" if status == "uploaded" else "MISSING"
            text += f"  {icon} {doc_type.replace('_', ' ').title()}: {status_text}\n"
        
        # Anomalies and Issues
        anomalies = analytics.get('anomalies', [])
        if anomalies:
            text += f"""

═══════════════════════════════════════════════════════════════════════════
                    ANOMALIES DETECTED ({len(anomalies)})
═══════════════════════════════════════════════════════════════════════════

"""
            # Group by severity
            high_severity = [a for a in anomalies if a.get('severity') == 'high']
            medium_severity = [a for a in anomalies if a.get('severity') == 'medium']
            
            if high_severity:
                text += "HIGH SEVERITY ISSUES:\n"
                for i, anomaly in enumerate(high_severity, 1):
                    text += f"\n  {i}. {anomaly.get('type', 'Unknown').replace('_', ' ').upper()}\n"
                    text += f"     File: {anomaly.get('filename', 'N/A')}\n"
                    text += f"     Description: {anomaly.get('description', 'N/A')}\n"
                    text += f"     Recommendation: {anomaly.get('recommendation', 'Review this issue')}\n"
            
            if medium_severity:
                text += "\nMEDIUM SEVERITY ISSUES:\n"
                for i, anomaly in enumerate(medium_severity, 1):
                    text += f"\n  {i}. {anomaly.get('type', 'Unknown').replace('_', ' ').upper()}\n"
                    text += f"     File: {anomaly.get('filename', 'N/A')}\n"
                    text += f"     Description: {anomaly.get('description', 'N/A')}\n"
                    text += f"     Recommendation: {anomaly.get('recommendation', 'Review this issue')}\n"
        else:
            text += f"""

═══════════════════════════════════════════════════════════════════════════
                         DATA QUALITY ANALYSIS
═══════════════════════════════════════════════════════════════════════════

✓ No anomalies detected in the uploaded data
✓ All data appears to be within normal ranges
✓ No missing or duplicate values found

"""
        
        # Recommendations
        text += f"""

═══════════════════════════════════════════════════════════════════════════
                          RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════

"""
        for i, rec in enumerate(report_data['recommendations'], 1):
            text += f"  {i}. {rec}\n"
        
        # Next Steps
        text += f"""

═══════════════════════════════════════════════════════════════════════════
                            NEXT STEPS
═══════════════════════════════════════════════════════════════════════════

"""
        if summary['status'] == 'COMPLETE':
            text += """  ✓ All required documents have been uploaded
  ✓ Review the anomalies section above (if any)
  ✓ Verify financial totals match your records
  ✓ Proceed with month-end close procedures
  ✓ Archive this report for audit purposes
"""
        elif summary['status'] == 'NEARLY_COMPLETE':
            text += f"""  • Upload remaining documents: {', '.join(summary['checklist_completion'].get('missing', []))}
  • Review and resolve any detected anomalies
  • Verify data completeness
  • Re-generate report after uploading missing documents
"""
        else:
            text += f"""  • Upload missing required documents: {', '.join([d for d, s in report_data['checklist'].items() if s == 'missing'])}
  • Ensure all CSV files are properly formatted
  • Review data quality before proceeding
  • Contact support if you encounter issues
"""
        
        text += f"""

═══════════════════════════════════════════════════════════════════════════
                          END OF REPORT
═══════════════════════════════════════════════════════════════════════════

This report was automatically generated by the Smart Month-End Close system.
For questions or support, please contact your system administrator.

"""
        
        return text


# Global instance
report_service = ReportService()
