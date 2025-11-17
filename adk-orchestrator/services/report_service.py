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


# Global instance
report_service = ReportService()
