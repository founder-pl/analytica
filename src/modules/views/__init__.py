"""
ANALYTICA Views Module
======================

DSL atoms for generating view specifications that can be rendered by frontend.

Atoms:
- view.chart - Generate chart specification
- view.table - Generate table specification  
- view.card - Generate metric card specification
- view.kpi - Generate KPI widget specification
- view.grid - Generate grid layout specification
- view.dashboard - Generate complete dashboard specification
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    DONUT = "donut"
    GAUGE = "gauge"


class CardStyle(str, Enum):
    DEFAULT = "default"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    INFO = "info"


@dataclass
class ViewSpec:
    """Base view specification"""
    type: str
    id: str = ""
    title: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class ChartSpec(ViewSpec):
    """Chart view specification"""
    chart_type: str = "bar"
    x_field: str = ""
    y_field: str = ""
    series: List[str] = None
    colors: List[str] = None
    show_legend: bool = True
    show_grid: bool = True
    animate: bool = True
    
    def __post_init__(self):
        self.type = "chart"
        if self.series is None:
            self.series = []
        if self.colors is None:
            self.colors = []


@dataclass
class TableSpec(ViewSpec):
    """Table view specification"""
    columns: List[Dict] = None
    sortable: bool = True
    filterable: bool = True
    paginate: bool = True
    page_size: int = 10
    striped: bool = True
    
    def __post_init__(self):
        self.type = "table"
        if self.columns is None:
            self.columns = []


@dataclass
class CardSpec(ViewSpec):
    """Metric card specification"""
    value_field: str = ""
    format: str = ""
    icon: str = ""
    style: str = "default"
    trend_field: str = ""
    trend_direction: str = ""
    
    def __post_init__(self):
        self.type = "card"


@dataclass 
class KPISpec(ViewSpec):
    """KPI widget specification"""
    value_field: str = ""
    target_field: str = ""
    format: str = ""
    icon: str = ""
    show_progress: bool = True
    show_sparkline: bool = False
    
    def __post_init__(self):
        self.type = "kpi"


@dataclass
class GridSpec(ViewSpec):
    """Grid layout specification"""
    columns: int = 2
    gap: int = 16
    items: List[Dict] = None
    
    def __post_init__(self):
        self.type = "grid"
        if self.items is None:
            self.items = []


@dataclass
class DashboardSpec(ViewSpec):
    """Dashboard specification"""
    layout: str = "grid"
    widgets: List[Dict] = None
    refresh_interval: int = 0
    
    def __post_init__(self):
        self.type = "dashboard"
        if self.widgets is None:
            self.widgets = []


class ViewsModule:
    """Views module for DSL atoms"""
    
    def __init__(self):
        self.name = "views"
        self._view_counter = 0
    
    def _generate_id(self, prefix: str) -> str:
        self._view_counter += 1
        return f"{prefix}_{self._view_counter}"
    
    def get_atoms(self) -> Dict[str, callable]:
        return {
            "view.chart": self.chart,
            "view.table": self.table,
            "view.card": self.card,
            "view.kpi": self.kpi,
            "view.grid": self.grid,
            "view.dashboard": self.dashboard,
            "view.text": self.text,
            "view.list": self.list_view,
        }
    
    def chart(self, data: Any = None, **kwargs) -> Dict:
        """
        Generate chart view specification.
        
        Args:
            data: Input data (passed through)
            type: Chart type (bar, line, pie, area, scatter, donut, gauge)
            x: X-axis field name
            y: Y-axis field name  
            series: List of series field names
            title: Chart title
            colors: Custom color palette
            
        Returns:
            Dict with data and view specification
        """
        chart_type = kwargs.get("type", kwargs.get("_arg0", "bar"))
        x_field = kwargs.get("x", kwargs.get("x_field", ""))
        y_field = kwargs.get("y", kwargs.get("y_field", ""))
        series = kwargs.get("series", [])
        title = kwargs.get("title", "")
        colors = kwargs.get("colors", [])
        show_legend = kwargs.get("legend", True)
        
        spec = ChartSpec(
            id=self._generate_id("chart"),
            title=title,
            chart_type=chart_type,
            x_field=x_field,
            y_field=y_field,
            series=series if isinstance(series, list) else [series],
            colors=colors if isinstance(colors, list) else [colors],
            show_legend=show_legend,
        )
        
        return self._wrap_result(data, spec)
    
    def table(self, data: Any = None, **kwargs) -> Dict:
        """
        Generate table view specification.
        
        Args:
            data: Input data (passed through)
            columns: List of column definitions or field names
            title: Table title
            sortable: Enable sorting
            filterable: Enable filtering
            paginate: Enable pagination
            page_size: Rows per page
            
        Returns:
            Dict with data and view specification
        """
        columns_input = kwargs.get("columns", kwargs.get("_arg0", []))
        title = kwargs.get("title", "")
        sortable = kwargs.get("sortable", True)
        filterable = kwargs.get("filterable", True)
        paginate = kwargs.get("paginate", True)
        page_size = kwargs.get("page_size", 10)
        
        # Convert simple column names to column specs
        columns = []
        if isinstance(columns_input, list):
            for col in columns_input:
                if isinstance(col, str):
                    columns.append({"field": col, "header": col.replace("_", " ").title()})
                elif isinstance(col, dict):
                    columns.append(col)
        
        # Auto-detect columns from data if not specified
        if not columns and isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                columns = [{"field": k, "header": k.replace("_", " ").title()} 
                          for k in data[0].keys()]
        
        spec = TableSpec(
            id=self._generate_id("table"),
            title=title,
            columns=columns,
            sortable=sortable,
            filterable=filterable,
            paginate=paginate,
            page_size=page_size,
        )
        
        return self._wrap_result(data, spec)
    
    def card(self, data: Any = None, **kwargs) -> Dict:
        """
        Generate metric card specification.
        
        Args:
            data: Input data (passed through)
            value: Field name for main value
            title: Card title
            format: Value format (number, currency, percent)
            icon: Icon name
            style: Card style (default, success, warning, danger, info)
            trend: Field name for trend value
            
        Returns:
            Dict with data and view specification
        """
        value_field = kwargs.get("value", kwargs.get("_arg0", ""))
        title = kwargs.get("title", "")
        format_str = kwargs.get("format", "")
        icon = kwargs.get("icon", "")
        style = kwargs.get("style", "default")
        trend_field = kwargs.get("trend", "")
        
        spec = CardSpec(
            id=self._generate_id("card"),
            title=title,
            value_field=value_field,
            format=format_str,
            icon=icon,
            style=style,
            trend_field=trend_field,
        )
        
        return self._wrap_result(data, spec)
    
    def kpi(self, data: Any = None, **kwargs) -> Dict:
        """
        Generate KPI widget specification.
        
        Args:
            data: Input data (passed through)
            value: Field name for current value
            target: Field name for target value
            title: KPI title
            format: Value format
            icon: Icon name
            
        Returns:
            Dict with data and view specification
        """
        value_field = kwargs.get("value", kwargs.get("_arg0", ""))
        target_field = kwargs.get("target", "")
        title = kwargs.get("title", "")
        format_str = kwargs.get("format", "")
        icon = kwargs.get("icon", "")
        show_progress = kwargs.get("progress", True)
        
        spec = KPISpec(
            id=self._generate_id("kpi"),
            title=title,
            value_field=value_field,
            target_field=target_field,
            format=format_str,
            icon=icon,
            show_progress=show_progress,
        )
        
        return self._wrap_result(data, spec)
    
    def grid(self, data: Any = None, **kwargs) -> Dict:
        """
        Generate grid layout specification.
        
        Args:
            data: Input data (passed through)
            columns: Number of columns
            gap: Gap between items in pixels
            items: List of view specifications
            
        Returns:
            Dict with data and view specification
        """
        columns = kwargs.get("columns", kwargs.get("_arg0", 2))
        gap = kwargs.get("gap", 16)
        items = kwargs.get("items", [])
        title = kwargs.get("title", "")
        
        spec = GridSpec(
            id=self._generate_id("grid"),
            title=title,
            columns=columns,
            gap=gap,
            items=items,
        )
        
        return self._wrap_result(data, spec)
    
    def dashboard(self, data: Any = None, **kwargs) -> Dict:
        """
        Generate dashboard specification.
        
        Args:
            data: Input data (passed through)
            layout: Layout type (grid, flex, stack)
            widgets: List of widget specifications
            title: Dashboard title
            refresh: Auto-refresh interval in seconds
            
        Returns:
            Dict with data and view specification
        """
        layout = kwargs.get("layout", kwargs.get("_arg0", "grid"))
        widgets = kwargs.get("widgets", [])
        title = kwargs.get("title", "")
        refresh = kwargs.get("refresh", 0)
        
        spec = DashboardSpec(
            id=self._generate_id("dashboard"),
            title=title,
            layout=layout,
            widgets=widgets,
            refresh_interval=refresh,
        )
        
        return self._wrap_result(data, spec)
    
    def text(self, data: Any = None, **kwargs) -> Dict:
        """
        Generate text/markdown view specification.
        
        Args:
            data: Input data (passed through)
            content: Text content or field name
            format: Format type (text, markdown, html)
            
        Returns:
            Dict with data and view specification
        """
        content = kwargs.get("content", kwargs.get("_arg0", ""))
        format_type = kwargs.get("format", "text")
        title = kwargs.get("title", "")
        
        spec = {
            "type": "text",
            "id": self._generate_id("text"),
            "title": title,
            "content": content,
            "format": format_type,
        }
        
        return self._wrap_result(data, spec)
    
    def list_view(self, data: Any = None, **kwargs) -> Dict:
        """
        Generate list view specification.
        
        Args:
            data: Input data (passed through)
            item_template: Template for list items
            title: List title
            
        Returns:
            Dict with data and view specification
        """
        title = kwargs.get("title", "")
        primary_field = kwargs.get("primary", kwargs.get("_arg0", ""))
        secondary_field = kwargs.get("secondary", "")
        icon_field = kwargs.get("icon", "")
        
        spec = {
            "type": "list",
            "id": self._generate_id("list"),
            "title": title,
            "primary_field": primary_field,
            "secondary_field": secondary_field,
            "icon_field": icon_field,
        }
        
        return self._wrap_result(data, spec)
    
    def _wrap_result(self, data: Any, spec: Union[ViewSpec, Dict]) -> Dict:
        """Wrap data and view spec into result format"""
        view_dict = spec.to_dict() if hasattr(spec, 'to_dict') else spec
        
        # If data already has views, append to them
        if isinstance(data, dict) and "views" in data:
            data["views"].append(view_dict)
            return data
        
        # Otherwise create new result structure
        return {
            "data": data,
            "views": [view_dict]
        }


# Singleton instance
_module = ViewsModule()


def get_module():
    return _module


def get_atoms():
    return _module.get_atoms()
