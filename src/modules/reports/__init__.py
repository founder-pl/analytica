"""
ANALYTICA Reports Module
========================
Report generation, scheduling, and distribution.

Features:
- Multiple output formats (PDF, Excel, HTML, JSON)
- Template-based reports
- Scheduled report generation
- Email/webhook distribution
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from .. import BaseModule


class ReportFormat(Enum):
    """Report output formats"""
    PDF = "pdf"
    EXCEL = "excel"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class ReportFrequency(Enum):
    """Report scheduling frequency"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass
class ReportTemplate:
    """Report template definition"""
    id: str
    name: str
    description: str = ""
    sections: List[str] = field(default_factory=list)
    default_format: ReportFormat = ReportFormat.PDF
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sections": self.sections,
            "default_format": self.default_format.value,
        }


@dataclass
class Report:
    """Generated report"""
    id: str
    template_id: str
    name: str
    format: ReportFormat
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "template_id": self.template_id,
            "name": self.name,
            "format": self.format.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ScheduledReport:
    """Scheduled report configuration"""
    id: str
    template_id: str
    frequency: ReportFrequency
    recipients: List[str]
    next_run: datetime
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "template_id": self.template_id,
            "frequency": self.frequency.value,
            "recipients": self.recipients,
            "next_run": self.next_run.isoformat(),
            "enabled": self.enabled,
        }


class ReportGenerator:
    """Report generation utilities"""
    
    @staticmethod
    def generate_html(title: str, data: Dict[str, Any], sections: List[str] = None) -> str:
        """Generate HTML report"""
        sections = sections or list(data.keys())
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 1px solid #ddd; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        .metric {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
"""
        
        for section in sections:
            if section in data:
                html += f"    <h2>{section.replace('_', ' ').title()}</h2>\n"
                section_data = data[section]
                
                if isinstance(section_data, dict):
                    html += "    <table>\n"
                    for key, value in section_data.items():
                        html += f"        <tr><th>{key}</th><td>{value}</td></tr>\n"
                    html += "    </table>\n"
                elif isinstance(section_data, list):
                    if section_data and isinstance(section_data[0], dict):
                        html += "    <table>\n"
                        html += "        <tr>"
                        for key in section_data[0].keys():
                            html += f"<th>{key}</th>"
                        html += "</tr>\n"
                        for item in section_data:
                            html += "        <tr>"
                            for value in item.values():
                                html += f"<td>{value}</td>"
                            html += "</tr>\n"
                        html += "    </table>\n"
                    else:
                        html += f"    <ul>\n"
                        for item in section_data:
                            html += f"        <li>{item}</li>\n"
                        html += "    </ul>\n"
                else:
                    html += f"    <p class='metric'>{section_data}</p>\n"
        
        html += "</body>\n</html>"
        return html
    
    @staticmethod
    def generate_json(title: str, data: Dict[str, Any]) -> str:
        """Generate JSON report"""
        return json.dumps({
            "title": title,
            "generated_at": datetime.utcnow().isoformat(),
            "data": data,
        }, indent=2, default=str)
    
    @staticmethod
    def generate_csv(data: List[Dict[str, Any]]) -> str:
        """Generate CSV from list of dicts"""
        if not data:
            return ""
        
        headers = list(data[0].keys())
        lines = [",".join(headers)]
        
        for row in data:
            values = [str(row.get(h, "")) for h in headers]
            lines.append(",".join(values))
        
        return "\n".join(lines)


class ReportsModule(BaseModule):
    """Reports module implementation"""
    
    name = "reports"
    version = "1.0.0"
    
    def __init__(self):
        self._templates: Dict[str, ReportTemplate] = {
            "executive_summary": ReportTemplate(
                id="executive_summary",
                name="Executive Summary",
                description="High-level overview for executives",
                sections=["summary", "key_metrics", "recommendations"],
            ),
            "financial_report": ReportTemplate(
                id="financial_report",
                name="Financial Report",
                description="Detailed financial analysis",
                sections=["income", "expenses", "balance", "trends"],
            ),
            "budget_variance": ReportTemplate(
                id="budget_variance",
                name="Budget Variance Report",
                description="Planned vs actual budget comparison",
                sections=["overview", "by_category", "variances", "actions"],
            ),
        }
        self._reports: Dict[str, Report] = {}
        self._scheduled: Dict[str, ScheduledReport] = {}
    
    def get_routes(self) -> List[Any]:
        return []
    
    def get_atoms(self) -> Dict[str, Any]:
        return {
            "report.generate": self.generate,
            "report.schedule": self.schedule,
            "report.send": self.send,
            "report.list": self.list_templates,
        }
    
    def generate(self, **kwargs) -> Dict[str, Any]:
        """Generate a report"""
        from uuid import uuid4
        
        template_id = kwargs.get("template", kwargs.get("_arg0", "executive_summary"))
        format_str = kwargs.get("format", kwargs.get("_arg1", "html"))
        data = kwargs.get("data", {})
        title = kwargs.get("title", "Report")
        
        report_format = ReportFormat(format_str) if format_str in [f.value for f in ReportFormat] else ReportFormat.HTML
        template = self._templates.get(template_id)
        
        report_id = f"report_{uuid4().hex[:8]}"
        
        # Generate content based on format
        if report_format == ReportFormat.HTML:
            content = ReportGenerator.generate_html(title, data, template.sections if template else None)
        elif report_format == ReportFormat.JSON:
            content = ReportGenerator.generate_json(title, data)
        elif report_format == ReportFormat.CSV and isinstance(data, list):
            content = ReportGenerator.generate_csv(data)
        else:
            content = json.dumps(data, indent=2, default=str)
        
        report = Report(
            id=report_id,
            template_id=template_id,
            name=title,
            format=report_format,
            data=data,
        )
        self._reports[report_id] = report
        
        return {
            "report_id": report_id,
            "format": report_format.value,
            "content": content[:1000] + "..." if len(content) > 1000 else content,
            "full_length": len(content),
            "created_at": report.created_at.isoformat(),
        }
    
    def schedule(self, **kwargs) -> Dict[str, Any]:
        """Schedule a report"""
        from uuid import uuid4
        
        template_id = kwargs.get("template", "executive_summary")
        frequency_str = kwargs.get("frequency", "weekly")
        recipients = kwargs.get("recipients", [])
        
        frequency = ReportFrequency(frequency_str) if frequency_str in [f.value for f in ReportFrequency] else ReportFrequency.WEEKLY
        
        # Calculate next run
        now = datetime.utcnow()
        if frequency == ReportFrequency.DAILY:
            next_run = now + timedelta(days=1)
        elif frequency == ReportFrequency.WEEKLY:
            next_run = now + timedelta(weeks=1)
        elif frequency == ReportFrequency.MONTHLY:
            next_run = now + timedelta(days=30)
        elif frequency == ReportFrequency.QUARTERLY:
            next_run = now + timedelta(days=90)
        else:
            next_run = now
        
        schedule_id = f"sched_{uuid4().hex[:8]}"
        scheduled = ScheduledReport(
            id=schedule_id,
            template_id=template_id,
            frequency=frequency,
            recipients=recipients,
            next_run=next_run,
        )
        self._scheduled[schedule_id] = scheduled
        
        return scheduled.to_dict()
    
    def send(self, **kwargs) -> Dict[str, Any]:
        """Send a report (mock)"""
        report_id = kwargs.get("report_id", kwargs.get("_arg0"))
        recipients = kwargs.get("recipients", kwargs.get("_arg1", []))
        method = kwargs.get("method", "email")
        
        return {
            "status": "sent",
            "report_id": report_id,
            "recipients": recipients,
            "method": method,
            "sent_at": datetime.utcnow().isoformat(),
        }
    
    def list_templates(self, **kwargs) -> Dict[str, Any]:
        """List available report templates"""
        return {
            "templates": [t.to_dict() for t in self._templates.values()],
            "count": len(self._templates),
        }


# Module instance
reports_module = ReportsModule()

__all__ = [
    "ReportsModule",
    "Report",
    "ReportTemplate",
    "ScheduledReport",
    "ReportFormat",
    "ReportFrequency",
    "ReportGenerator",
    "reports_module",
]
