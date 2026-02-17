"""Timezone utilities for campaign scheduling."""
from datetime import datetime, time as dt_time
from typing import Optional
import pytz
from zoneinfo import ZoneInfo


class TimezoneHelper:
    """Helper for timezone-aware scheduling."""
    
    @staticmethod
    def validate_timezone(timezone_str: str) -> bool:
        """
        Validate if timezone string is valid.
        
        Args:
            timezone_str: IANA timezone string (e.g., "America/New_York")
            
        Returns:
            True if valid timezone
        """
        try:
            pytz.timezone(timezone_str)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False
    
    @staticmethod
    def convert_to_timezone(dt: datetime, timezone_str: str) -> datetime:
        """
        Convert datetime to specific timezone.
        
        Args:
            dt: Datetime to convert
            timezone_str: Target timezone
            
        Returns:
            Datetime in target timezone
        """
        if dt.tzinfo is None:
            # Assume UTC if no timezone
            dt = pytz.UTC.localize(dt)
        
        target_tz = pytz.timezone(timezone_str)
        return dt.astimezone(target_tz)
    
    @staticmethod
    def get_current_time_in_timezone(timezone_str: str) -> datetime:
        """
        Get current time in specific timezone.
        
        Args:
            timezone_str: Target timezone
            
        Returns:
            Current datetime in target timezone
        """
        tz = pytz.timezone(timezone_str)
        return datetime.now(tz)
    
    @staticmethod
    def is_within_schedule(
        current_time: datetime,
        start_hour: int,
        end_hour: int,
        allowed_days: list[int],
        blackout_dates: Optional[list[str]] = None
    ) -> bool:
        """
        Check if current time is within allowed schedule.
        
        Args:
            current_time: Current datetime (timezone-aware)
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)
            allowed_days: List of allowed weekdays (0=Monday, 6=Sunday)
            blackout_dates: List of blackout dates in YYYY-MM-DD format
            
        Returns:
            True if within schedule
        """
        # Check day of week (0=Monday, 6=Sunday)
        if current_time.weekday() not in allowed_days:
            return False
        
        # Check hour
        current_hour = current_time.hour
        if not (start_hour <= current_hour < end_hour):
            return False
        
        # Check blackout dates
        if blackout_dates:
            current_date = current_time.strftime("%Y-%m-%d")
            if current_date in blackout_dates:
                return False
        
        return True
    
    @staticmethod
    def get_next_available_time(
        current_time: datetime,
        start_hour: int,
        end_hour: int,
        allowed_days: list[int],
        timezone_str: str
    ) -> datetime:
        """
        Get next available time within schedule.
        
        Args:
            current_time: Current datetime
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)
            allowed_days: List of allowed weekdays
            timezone_str: Timezone string
            
        Returns:
            Next available datetime
        """
        tz = pytz.timezone(timezone_str)
        next_time = current_time
        
        # Try up to 14 days ahead
        for _ in range(14):
            # Check if current day is allowed
            if next_time.weekday() in allowed_days:
                # If before start hour, set to start hour
                if next_time.hour < start_hour:
                    next_time = next_time.replace(hour=start_hour, minute=0, second=0)
                    return next_time
                # If within window, return current time
                elif next_time.hour < end_hour:
                    return next_time
            
            # Move to next day at start hour
            next_time = (next_time + pytz.timedelta(days=1)).replace(
                hour=start_hour, minute=0, second=0
            )
        
        # If no slot found in 14 days, return 1 day ahead
        return current_time + pytz.timedelta(days=1)


# Global timezone helper instance
timezone_helper = TimezoneHelper()
