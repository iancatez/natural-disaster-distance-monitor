"""
Data models for the Natural Disaster Distance Monitor.

This module defines all data structures used throughout the application:
- Enums for disaster types and severity classifications
- Data classes for locations and disaster results
- Serialization methods for JSON output
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


# =============================================================================
# Enums - Disaster Types
# =============================================================================

class DisasterType(Enum):
    """Types of natural disasters tracked by the system."""
    HURRICANE = "hurricane"
    TORNADO = "tornado"
    WILDFIRE = "wildfire"


# =============================================================================
# Enums - Severity Classifications
# =============================================================================

class HurricaneCategory(Enum):
    """
    Saffir-Simpson Hurricane Wind Scale categories.
    
    Also includes Tropical Depression and Tropical Storm classifications.
    """
    TROPICAL_DEPRESSION = "TD"
    TROPICAL_STORM = "TS"
    CATEGORY_1 = "1"
    CATEGORY_2 = "2"
    CATEGORY_3 = "3"
    CATEGORY_4 = "4"
    CATEGORY_5 = "5"
    
    @classmethod
    def from_wind_speed(cls, wind_mph: float) -> 'HurricaneCategory':
        """Determine category from maximum sustained wind speed."""
        if wind_mph < 39:
            return cls.TROPICAL_DEPRESSION
        elif wind_mph < 74:
            return cls.TROPICAL_STORM
        elif wind_mph < 96:
            return cls.CATEGORY_1
        elif wind_mph < 111:
            return cls.CATEGORY_2
        elif wind_mph < 130:
            return cls.CATEGORY_3
        elif wind_mph < 157:
            return cls.CATEGORY_4
        else:
            return cls.CATEGORY_5
    
    @classmethod
    def from_ssnum(cls, ssnum: int) -> 'HurricaneCategory':
        """Determine category from Saffir-Simpson number."""
        mapping = {
            -2: cls.TROPICAL_DEPRESSION,
            -1: cls.TROPICAL_STORM,
            0: cls.TROPICAL_STORM,
            1: cls.CATEGORY_1,
            2: cls.CATEGORY_2,
            3: cls.CATEGORY_3,
            4: cls.CATEGORY_4,
            5: cls.CATEGORY_5,
        }
        return mapping.get(ssnum, cls.TROPICAL_STORM)
    
    @property
    def description(self) -> str:
        """Human-readable description of the category."""
        descriptions = {
            self.TROPICAL_DEPRESSION: "Tropical Depression",
            self.TROPICAL_STORM: "Tropical Storm",
            self.CATEGORY_1: "Category 1 Hurricane",
            self.CATEGORY_2: "Category 2 Hurricane",
            self.CATEGORY_3: "Category 3 Hurricane (Major)",
            self.CATEGORY_4: "Category 4 Hurricane (Major)",
            self.CATEGORY_5: "Category 5 Hurricane (Major)",
        }
        return descriptions.get(self, "Unknown")


class TornadoScale(Enum):
    """
    Enhanced Fujita (EF) Scale for tornado intensity.
    """
    EF0 = 0
    EF1 = 1
    EF2 = 2
    EF3 = 3
    EF4 = 4
    EF5 = 5
    
    @classmethod
    def from_efnum(cls, efnum: int) -> Optional['TornadoScale']:
        """Create TornadoScale from EF number."""
        try:
            return cls(efnum)
        except ValueError:
            return None
    
    @property
    def description(self) -> str:
        """Human-readable description of the EF rating."""
        descriptions = {
            self.EF0: "EF0 - Light Damage (65-85 mph)",
            self.EF1: "EF1 - Moderate Damage (86-110 mph)",
            self.EF2: "EF2 - Significant Damage (111-135 mph)",
            self.EF3: "EF3 - Severe Damage (136-165 mph)",
            self.EF4: "EF4 - Devastating Damage (166-200 mph)",
            self.EF5: "EF5 - Incredible Damage (200+ mph)",
        }
        return descriptions.get(self, "Unknown")


class WildfireSize(Enum):
    """
    Wildfire size classifications based on acreage.
    """
    SMALL = "small"       # < 100 acres
    MEDIUM = "medium"     # 100-1,000 acres
    LARGE = "large"       # 1,000-10,000 acres
    MAJOR = "major"       # 10,000-100,000 acres
    MEGA = "mega"         # 100,000+ acres
    
    @classmethod
    def from_acres(cls, acres: float) -> 'WildfireSize':
        """Determine size category from acreage."""
        if acres < 100:
            return cls.SMALL
        elif acres < 1000:
            return cls.MEDIUM
        elif acres < 10000:
            return cls.LARGE
        elif acres < 100000:
            return cls.MAJOR
        else:
            return cls.MEGA
    
    @property
    def description(self) -> str:
        """Human-readable description of the size category."""
        descriptions = {
            self.SMALL: "Small Fire (< 100 acres)",
            self.MEDIUM: "Medium Fire (100-1,000 acres)",
            self.LARGE: "Large Fire (1,000-10,000 acres)",
            self.MAJOR: "Major Fire (10,000-100,000 acres)",
            self.MEGA: "Megafire (100,000+ acres)",
        }
        return descriptions.get(self, "Unknown")


# =============================================================================
# Data Classes - Location
# =============================================================================

@dataclass
class Location:
    """
    A geographic location for disaster queries.
    
    Attributes:
        name: Human-readable location name
        latitude: Decimal degrees (-90 to 90)
        longitude: Decimal degrees (-180 to 180)
    """
    name: str
    latitude: float
    longitude: float
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Location':
        """Create Location from dictionary."""
        return cls(
            name=data.get('name', data.get('location', 'Unknown')),
            latitude=float(data['latitude']),
            longitude=float(data['longitude'])
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude
        }


# =============================================================================
# Data Classes - Disaster Results
# =============================================================================

@dataclass
class DisasterResult:
    """
    Base class for all disaster result types.
    
    Contains common fields shared by all disaster types.
    """
    disaster_type: DisasterType
    name: str
    distance_miles: float
    latitude: float
    longitude: float
    severity: str
    details: Dict[str, Any] = field(default_factory=dict)
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'disaster_type': self.disaster_type.value,
            'name': self.name,
            'distance_miles': round(self.distance_miles, 2),
            'latitude': round(self.latitude, 4),
            'longitude': round(self.longitude, 4),
            'severity': self.severity,
            'details': self.details,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


@dataclass
class HurricaneResult(DisasterResult):
    """
    Result for a hurricane/cyclone query.
    
    Extends DisasterResult with hurricane-specific fields.
    """
    category: Optional[HurricaneCategory] = None
    max_wind_mph: Optional[float] = None
    gust_mph: Optional[float] = None
    movement_direction: Optional[str] = None
    movement_speed_mph: Optional[float] = None
    advisory_number: Optional[str] = None
    basin: Optional[str] = None
    storm_type: Optional[str] = None
    inside_cone: bool = False
    
    def __post_init__(self):
        """Ensure disaster_type is set correctly."""
        self.disaster_type = DisasterType.HURRICANE
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        base = super().to_dict()
        base.update({
            'category': self.category.value if self.category else None,
            'max_wind_mph': self.max_wind_mph,
            'gust_mph': self.gust_mph,
            'movement_direction': self.movement_direction,
            'movement_speed_mph': self.movement_speed_mph,
            'advisory_number': self.advisory_number,
            'basin': self.basin,
            'storm_type': self.storm_type,
            'inside_cone': self.inside_cone
        })
        return base


@dataclass
class TornadoResult(DisasterResult):
    """
    Result for a tornado query.
    
    Extends DisasterResult with tornado-specific fields.
    """
    ef_scale: Optional[TornadoScale] = None
    max_wind_mph: Optional[float] = None
    path_length_miles: Optional[float] = None
    path_width_yards: Optional[float] = None
    fatalities: Optional[int] = None
    injuries: Optional[int] = None
    storm_date: Optional[datetime] = None
    
    def __post_init__(self):
        """Ensure disaster_type is set correctly."""
        self.disaster_type = DisasterType.TORNADO
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        base = super().to_dict()
        base.update({
            'ef_scale': f"EF{self.ef_scale.value}" if self.ef_scale else None,
            'max_wind_mph': self.max_wind_mph,
            'path_length_miles': self.path_length_miles,
            'path_width_yards': self.path_width_yards,
            'fatalities': self.fatalities,
            'injuries': self.injuries,
            'storm_date': self.storm_date.isoformat() if self.storm_date else None
        })
        return base


@dataclass
class WildfireResult(DisasterResult):
    """
    Result for a wildfire query.
    
    Extends DisasterResult with wildfire-specific fields.
    """
    size_category: Optional[WildfireSize] = None
    acres: Optional[float] = None
    containment_percent: Optional[float] = None
    inside_perimeter: bool = False
    fire_id: Optional[str] = None
    
    def __post_init__(self):
        """Ensure disaster_type is set correctly."""
        self.disaster_type = DisasterType.WILDFIRE
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        base = super().to_dict()
        base.update({
            'size_category': self.size_category.value if self.size_category else None,
            'acres': round(self.acres, 1) if self.acres else None,
            'containment_percent': self.containment_percent,
            'inside_perimeter': self.inside_perimeter,
            'fire_id': self.fire_id
        })
        return base


# =============================================================================
# Data Classes - Aggregated Results
# =============================================================================

@dataclass
class LocationResults:
    """
    Aggregated results for a single location query.
    
    Contains all disasters found near a location, organized by type.
    """
    location: Location
    hurricanes: List[HurricaneResult] = field(default_factory=list)
    tornadoes: List[TornadoResult] = field(default_factory=list)
    wildfires: List[WildfireResult] = field(default_factory=list)
    radius_miles: float = 100.0
    query_time: Optional[datetime] = None
    
    @property
    def total_disasters(self) -> int:
        """Total number of disasters found."""
        return len(self.hurricanes) + len(self.tornadoes) + len(self.wildfires)
    
    @property
    def has_disasters(self) -> bool:
        """Whether any disasters were found."""
        return self.total_disasters > 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'query_time': self.query_time.isoformat() if self.query_time else None,
            'location': self.location.to_dict(),
            'radius_miles': self.radius_miles,
            'results': {
                'hurricanes': [h.to_dict() for h in self.hurricanes],
                'tornadoes': [t.to_dict() for t in self.tornadoes],
                'wildfires': [w.to_dict() for w in self.wildfires]
            },
            'summary': {
                'total_disasters': self.total_disasters,
                'hurricanes_count': len(self.hurricanes),
                'tornadoes_count': len(self.tornadoes),
                'wildfires_count': len(self.wildfires)
            }
        }

