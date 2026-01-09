#!/usr/bin/env python3
"""
Natural Disaster Distance Monitor - CLI Interface

Find hurricanes, tornadoes, and wildfires near any location.

Usage Examples:
    # Interactive mode (no arguments)
    python main.py
    
    # Single location query
    python main.py --lat 29.7604 --lon -95.3698
    python main.py --lat 29.7604 --lon -95.3698 --name "Houston TX"
    python main.py --lat 29.7604 --lon -95.3698 --radius 50
    
    # Filter by disaster type
    python main.py --lat 29.7604 --lon -95.3698 --type hurricanes
    python main.py --lat 29.7604 --lon -95.3698 --type hurricanes --type wildfires
    
    # Batch query from CSV file
    python main.py --csv ../shared/data/test_locations.csv
    python main.py --csv ../shared/data/test_locations.csv --radius 50
    
    # Output formats
    python main.py --lat 29.7604 --lon -95.3698 --json
    python main.py --csv ../shared/data/test_locations.csv --output results.json
"""

import argparse
import json
import sys
import logging
from datetime import datetime
from typing import List, Optional

from disasters import (
    get_nearby_disasters,
    query_locations_from_csv,
    DisasterType,
    LocationResults,
    configure_logging,
)


def main():
    """Main entry point for the CLI."""
    # If no arguments provided, launch interactive mode
    if len(sys.argv) == 1:
        try:
            from interactive import main as interactive_main
            interactive_main()
            return
        except ImportError as e:
            print("Interactive mode requires 'rich' and 'questionary' packages.")
            print("Install with: pip install rich questionary")
            print(f"\nError: {e}")
            sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description='Find natural disasters near a location',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Interactive mode flag
    parser.add_argument(
        '--interactive', '-i', action='store_true',
        help='Launch interactive mode with menus and prompts'
    )
    
    # Location input options (mutually exclusive)
    location_group = parser.add_mutually_exclusive_group(required=False)
    location_group.add_argument(
        '--csv', type=str, metavar='FILE',
        help='CSV file with locations (columns: name, latitude, longitude)'
    )
    location_group.add_argument(
        '--lat', type=float,
        help='Latitude in decimal degrees (use with --lon)'
    )
    
    parser.add_argument(
        '--lon', type=float,
        help='Longitude in decimal degrees (use with --lat)'
    )
    parser.add_argument(
        '--name', type=str, default='Query Location',
        help='Name for the location (default: "Query Location")'
    )
    
    # Query options
    parser.add_argument(
        '--radius', type=float, default=100,
        help='Search radius in miles (default: 100)'
    )
    parser.add_argument(
        '--type', choices=['hurricanes', 'tornadoes', 'wildfires'],
        action='append', dest='types', metavar='TYPE',
        help='Disaster types to query (can repeat, default: all)'
    )
    
    # Output options
    parser.add_argument(
        '--json', action='store_true',
        help='Output as JSON to stdout'
    )
    parser.add_argument(
        '--output', '-o', type=str, metavar='FILE',
        help='Write JSON output to file'
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Suppress progress messages'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Show detailed progress messages'
    )
    
    args = parser.parse_args()
    
    # Handle interactive mode flag
    if args.interactive:
        try:
            from interactive import main as interactive_main
            interactive_main()
            return
        except ImportError as e:
            print("Interactive mode requires 'rich' and 'questionary' packages.")
            print("Install with: pip install rich questionary")
            sys.exit(1)
    
    # Require either --lat or --csv if not interactive
    if args.lat is None and args.csv is None:
        parser.error('Either --lat/--lon or --csv is required (or use --interactive)')
    
    # Validate lat/lon pair
    if args.lat is not None and args.lon is None:
        parser.error('--lat requires --lon')
    if args.lon is not None and args.lat is None:
        parser.error('--lon requires --lat')
    
    # Configure logging
    if args.quiet:
        log_level = logging.WARNING
    elif args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    configure_logging(log_level)
    
    # Convert type strings to enum
    disaster_types = None
    if args.types:
        type_map = {
            'hurricanes': DisasterType.HURRICANE,
            'tornadoes': DisasterType.TORNADO,
            'wildfires': DisasterType.WILDFIRE
        }
        disaster_types = [type_map[t] for t in args.types]
    
    # Execute query
    try:
        if args.csv:
            results = query_locations_from_csv(
                args.csv,
                radius_miles=args.radius,
                disaster_types=disaster_types
            )
        else:
            result = get_nearby_disasters(
                latitude=args.lat,
                longitude=args.lon,
                radius_miles=args.radius,
                disaster_types=disaster_types,
                name=args.name
            )
            results = [result]
        
        # Output results
        if args.json or args.output:
            output_json(results, args.output)
        else:
            output_table(results)
            
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def output_json(results: List[LocationResults], output_file: Optional[str] = None):
    """Output results as JSON."""
    if len(results) == 1:
        data = results[0].to_dict()
    else:
        data = {
            'query_time': datetime.now().isoformat(),
            'locations': [r.to_dict() for r in results],
            'summary': {
                'total_locations': len(results),
                'total_disasters': sum(r.total_disasters for r in results)
            }
        }
    
    json_str = json.dumps(data, indent=2, default=str)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(json_str)
        print(f"Results written to {output_file}")
    else:
        print(json_str)


def output_table(results: List[LocationResults]):
    """Output results as formatted table."""
    print()
    print("=" * 60)
    print("  NATURAL DISASTER DISTANCE MONITOR")
    print("=" * 60)
    
    for result in results:
        print()
        print(f"[*] Location: {result.location.name}")
        print(f"    Coordinates: ({result.location.latitude}, {result.location.longitude})")
        print(f"    Search Radius: {result.radius_miles} miles")
        print()
        
        # Hurricanes
        print(f"[HURRICANES] ({len(result.hurricanes)} found)")
        if result.hurricanes:
            for h in result.hurricanes:
                inside_str = " [INSIDE CONE]" if h.inside_cone else ""
                print(f"    * {h.name} - {h.distance_miles:.1f} miles{inside_str}")
                print(f"      {h.severity}")
                if h.max_wind_mph:
                    wind_info = f"Max Wind: {h.max_wind_mph:.0f} mph"
                    if h.movement_direction and h.movement_speed_mph:
                        wind_info += f", Moving {h.movement_direction} at {h.movement_speed_mph:.0f} mph"
                    print(f"      {wind_info}")
        else:
            print("    No hurricanes within search radius.")
        print()
        
        # Tornadoes
        print(f"[TORNADOES] ({len(result.tornadoes)} found)")
        if result.tornadoes:
            for t in result.tornadoes:
                ef_str = f"EF{t.ef_scale.value}" if t.ef_scale else "Unknown"
                date_str = t.storm_date.strftime("%Y-%m-%d") if t.storm_date else "Unknown date"
                print(f"    * {ef_str} - {t.distance_miles:.1f} miles ({date_str})")
                if t.path_length_miles and t.path_width_yards:
                    print(f"      Path: {t.path_length_miles:.1f} mi x {t.path_width_yards:.0f} yds")
                casualties = []
                if t.fatalities:
                    casualties.append(f"{t.fatalities} fatalities")
                if t.injuries:
                    casualties.append(f"{t.injuries} injuries")
                if casualties:
                    print(f"      Casualties: {', '.join(casualties)}")
        else:
            print("    No recent tornadoes within search radius.")
        print()
        
        # Wildfires
        print(f"[WILDFIRES] ({len(result.wildfires)} found)")
        if result.wildfires:
            for w in result.wildfires:
                inside_str = " [INSIDE PERIMETER]" if w.inside_perimeter else ""
                print(f"    * {w.name} - {w.distance_miles:.1f} miles{inside_str}")
                size_str = f"{w.acres:,.0f} acres" if w.acres else "Unknown size"
                contain_str = f", {w.containment_percent:.0f}% contained" if w.containment_percent is not None else ""
                print(f"      {size_str}{contain_str}")
        else:
            print("    No active wildfires within search radius.")
        
        print()
        print("-" * 60)
        print(f"    SUMMARY: {result.total_disasters} total disasters within {result.radius_miles} miles")
        if result.query_time:
            print(f"    Query Time: {result.query_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
    
    # Multi-location summary
    if len(results) > 1:
        print()
        print("=" * 60)
        print("  BATCH SUMMARY")
        print("=" * 60)
        print(f"   Locations Queried: {len(results)}")
        print(f"   Total Disasters Found: {sum(r.total_disasters for r in results)}")
        
        # Find location with most disasters
        if results:
            max_result = max(results, key=lambda r: r.total_disasters)
            if max_result.total_disasters > 0:
                print(f"   Most Affected: {max_result.location.name} ({max_result.total_disasters} disasters)")
        print("=" * 60)
    
    print()


if __name__ == '__main__':
    main()

