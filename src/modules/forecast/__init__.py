"""
ANALYTICA Forecast Module
=========================
Time series forecasting and trend analysis.

Features:
- Simple moving average
- Exponential smoothing
- Linear trend analysis
- Seasonal decomposition
- Multi-period forecasting
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
import statistics

from .. import BaseModule


class ForecastMethod(Enum):
    """Forecasting methods"""
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    SEASONAL = "seasonal"


class TrendDirection(Enum):
    """Trend directions"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


@dataclass
class ForecastPoint:
    """Single forecast point"""
    period: int
    value: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    confidence: float = 0.95
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "value": round(self.value, 2),
            "lower_bound": round(self.lower_bound, 2) if self.lower_bound else None,
            "upper_bound": round(self.upper_bound, 2) if self.upper_bound else None,
            "confidence": self.confidence,
        }


@dataclass
class ForecastResult:
    """Complete forecast result"""
    method: ForecastMethod
    historical: List[float]
    predictions: List[ForecastPoint]
    trend: TrendDirection
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method.value,
            "historical_count": len(self.historical),
            "predictions": [p.to_dict() for p in self.predictions],
            "trend": self.trend.value,
            "metrics": self.metrics,
        }


class ForecastCalculator:
    """Forecasting calculation utilities"""
    
    @staticmethod
    def moving_average(data: List[float], window: int = 3) -> List[float]:
        """Calculate moving average"""
        if len(data) < window:
            return data
        
        result = []
        for i in range(len(data) - window + 1):
            avg = sum(data[i:i + window]) / window
            result.append(round(avg, 2))
        return result
    
    @staticmethod
    def exponential_smoothing(data: List[float], alpha: float = 0.3) -> List[float]:
        """Calculate exponential smoothing"""
        if not data:
            return []
        
        result = [data[0]]
        for i in range(1, len(data)):
            smoothed = alpha * data[i] + (1 - alpha) * result[-1]
            result.append(round(smoothed, 2))
        return result
    
    @staticmethod
    def linear_trend(data: List[float]) -> Dict[str, float]:
        """Calculate linear trend (slope and intercept)"""
        n = len(data)
        if n < 2:
            return {"slope": 0, "intercept": data[0] if data else 0}
        
        x_mean = (n - 1) / 2
        y_mean = sum(data) / n
        
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(data))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        return {
            "slope": round(slope, 4),
            "intercept": round(intercept, 2),
        }
    
    @staticmethod
    def detect_trend(data: List[float], threshold: float = 0.01) -> TrendDirection:
        """Detect trend direction"""
        if len(data) < 2:
            return TrendDirection.STABLE
        
        trend = ForecastCalculator.linear_trend(data)
        slope_pct = trend["slope"] / (sum(data) / len(data)) if sum(data) != 0 else 0
        
        if slope_pct > threshold:
            return TrendDirection.UP
        elif slope_pct < -threshold:
            return TrendDirection.DOWN
        return TrendDirection.STABLE
    
    @staticmethod
    def forecast_next(
        data: List[float],
        periods: int = 1,
        method: ForecastMethod = ForecastMethod.LINEAR
    ) -> List[ForecastPoint]:
        """Forecast next N periods"""
        if not data:
            return []
        
        predictions = []
        
        if method == ForecastMethod.MOVING_AVERAGE:
            window = min(3, len(data))
            last_avg = sum(data[-window:]) / window
            std_dev = statistics.stdev(data) if len(data) > 1 else 0
            
            for i in range(periods):
                predictions.append(ForecastPoint(
                    period=len(data) + i + 1,
                    value=last_avg,
                    lower_bound=last_avg - 1.96 * std_dev,
                    upper_bound=last_avg + 1.96 * std_dev,
                ))
        
        elif method == ForecastMethod.EXPONENTIAL:
            smoothed = ForecastCalculator.exponential_smoothing(data)
            last_value = smoothed[-1] if smoothed else data[-1]
            std_dev = statistics.stdev(data) if len(data) > 1 else 0
            
            for i in range(periods):
                predictions.append(ForecastPoint(
                    period=len(data) + i + 1,
                    value=last_value,
                    lower_bound=last_value - 1.96 * std_dev,
                    upper_bound=last_value + 1.96 * std_dev,
                ))
        
        elif method == ForecastMethod.LINEAR:
            trend = ForecastCalculator.linear_trend(data)
            std_dev = statistics.stdev(data) if len(data) > 1 else 0
            
            for i in range(periods):
                future_x = len(data) + i
                forecast_value = trend["intercept"] + trend["slope"] * future_x
                
                predictions.append(ForecastPoint(
                    period=len(data) + i + 1,
                    value=forecast_value,
                    lower_bound=forecast_value - 1.96 * std_dev,
                    upper_bound=forecast_value + 1.96 * std_dev,
                ))
        
        return predictions
    
    @staticmethod
    def calculate_accuracy(actual: List[float], predicted: List[float]) -> Dict[str, float]:
        """Calculate forecast accuracy metrics"""
        if len(actual) != len(predicted) or not actual:
            return {}
        
        errors = [a - p for a, p in zip(actual, predicted)]
        abs_errors = [abs(e) for e in errors]
        pct_errors = [abs(e / a) * 100 if a != 0 else 0 for e, a in zip(errors, actual)]
        
        return {
            "mae": round(sum(abs_errors) / len(abs_errors), 2),  # Mean Absolute Error
            "mape": round(sum(pct_errors) / len(pct_errors), 2),  # Mean Absolute Percentage Error
            "rmse": round((sum(e ** 2 for e in errors) / len(errors)) ** 0.5, 2),  # Root Mean Square Error
        }


class ForecastModule(BaseModule):
    """Forecast module implementation"""
    
    name = "forecast"
    version = "1.0.0"
    
    def get_routes(self) -> List[Any]:
        return []
    
    def get_atoms(self) -> Dict[str, Any]:
        return {
            "forecast.predict": self.predict,
            "forecast.trend": self.analyze_trend,
            "forecast.smooth": self.smooth_data,
        }
    
    def predict(self, **kwargs) -> Dict[str, Any]:
        """Generate forecast predictions"""
        data = kwargs.get("data", kwargs.get("_arg0", []))
        periods = kwargs.get("periods", kwargs.get("_arg1", 3))
        method_str = kwargs.get("method", "linear")
        
        if isinstance(data, (int, float)):
            periods = data
            data = []
        
        method = ForecastMethod(method_str) if method_str in [m.value for m in ForecastMethod] else ForecastMethod.LINEAR
        
        # Convert to float list
        float_data = [float(d) for d in data] if data else []
        
        if not float_data:
            return {
                "predictions": [],
                "trend": "unknown",
                "message": "No historical data provided",
            }
        
        predictions = ForecastCalculator.forecast_next(float_data, periods, method)
        trend = ForecastCalculator.detect_trend(float_data)
        
        result = ForecastResult(
            method=method,
            historical=float_data,
            predictions=predictions,
            trend=trend,
        )
        
        return result.to_dict()
    
    def analyze_trend(self, **kwargs) -> Dict[str, Any]:
        """Analyze trend in data"""
        data = kwargs.get("data", kwargs.get("_arg0", []))
        float_data = [float(d) for d in data] if data else []
        
        if not float_data:
            return {"trend": "unknown", "slope": 0}
        
        trend = ForecastCalculator.detect_trend(float_data)
        linear = ForecastCalculator.linear_trend(float_data)
        
        return {
            "trend": trend.value,
            "slope": linear["slope"],
            "intercept": linear["intercept"],
            "data_points": len(float_data),
        }
    
    def smooth_data(self, **kwargs) -> Dict[str, Any]:
        """Apply smoothing to data"""
        data = kwargs.get("data", kwargs.get("_arg0", []))
        method = kwargs.get("method", "exponential")
        alpha = kwargs.get("alpha", 0.3)
        window = kwargs.get("window", 3)
        
        float_data = [float(d) for d in data] if data else []
        
        if method == "moving_average":
            smoothed = ForecastCalculator.moving_average(float_data, window)
        else:
            smoothed = ForecastCalculator.exponential_smoothing(float_data, alpha)
        
        return {
            "original": float_data,
            "smoothed": smoothed,
            "method": method,
        }


# Module instance
forecast_module = ForecastModule()

__all__ = [
    "ForecastModule",
    "ForecastResult",
    "ForecastPoint",
    "ForecastMethod",
    "TrendDirection",
    "ForecastCalculator",
    "forecast_module",
]
