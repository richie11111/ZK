import json
import pandas as pd
import os
import re
from datetime import datetime, timezone
import dateutil.parser

def parse_datetime(datetime_str):
    """
    Parse datetime string and return a tuple of (formatted datetime, timezone offset)
    
    :param datetime_str: ISO 8601 formatted datetime string
    :return: Tuple of (formatted datetime string, timezone offset string)
    """
    try:
        if not datetime_str:
            return None, None
        
        # Parse the datetime using dateutil
        parsed_dt = dateutil.parser.isoparse(datetime_str)
        
        # Format datetime with full precision including milliseconds
        formatted_dt = parsed_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Keep 3 decimal places for milliseconds
        
        # Extract timezone offset
        offset = parsed_dt.strftime('%z')
        
        # Format offset for readability (e.g., convert +0500 to +05:00)
        if offset:
            offset = f"{offset[:3]}:{offset[3:]}"
        
        return formatted_dt, offset
    except Exception as e:
        print(f"Error parsing datetime {datetime_str}: {e}")
        return None, None

def clean_and_parse_coordinates(point):
    """
    Clean and parse latitude and longitude from a string
    
    :param point: String containing latitude and longitude
    :return: Tuple of (cleaned_latitude, cleaned_longitude)
    """
    try:
        # Remove strange characters and degree symbol
        if isinstance(point, str):
            cleaned_point = point.encode('ascii', 'ignore').decode('ascii')
            cleaned_point = cleaned_point.replace('°', '').replace(' ', '')
            
            # Split coordinates
            coordinates = cleaned_point.split(',')
            if len(coordinates) == 2:
                # Attempt to convert to float
                lat = float(coordinates[0])
                lon = float(coordinates[1])
                return lat, lon
        return None, None
    except Exception as e:
        print(f"Error parsing coordinates {point}: {e}")
        return None, None

def convert_timeline_to_csv(json_file, csv_file):
    """
    Convert Timeline JSON to CSV, extracting and cleaning location points and semantic segments
    
    :param json_file: Input JSON file path
    :param csv_file: Output CSV file path
    """
    try:
        # Print current working directory and file paths for debugging
        print(f"Current Working Directory: {os.getcwd()}")
        print(f"Input JSON File: {json_file}")
        print(f"Output CSV File: {csv_file}")
        
        # Read the JSON file with proper encoding
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Prepare a list to store location and semantic segment data
        timeline_data = []
        
        # Process previous method for finding positions
        def find_positions(obj):
            positions = []
            
            if isinstance(obj, dict):
                # Check if this dictionary represents a position
                if 'LatLng' in obj and 'timestamp' in obj:
                    positions.append(obj)
                
                # Recursively search nested dictionaries
                for value in obj.values():
                    positions.extend(find_positions(value))
            
            elif isinstance(obj, list):
                # Search through list items
                for item in obj:
                    if isinstance(item, dict):
                        if 'LatLng' in item and 'timestamp' in item:
                            positions.append(item)
                    positions.extend(find_positions(item))
            
            return positions
        
        # Find all positions in the data
        found_positions = find_positions(data)
        
        print(f"\nFound {len(found_positions)} position entries")
        
        # Process found positions
        for position in found_positions:
            latlng = position.get('LatLng')
            lat, lon = clean_and_parse_coordinates(latlng)
            
            time, time_offset = parse_datetime(position.get('timestamp'))
            
            position_entry = {
                'Time': time,
                'Time Offset': time_offset,
                'Point': str(latlng),
                'Latitude': lat,
                'Longitude': lon,
                'Accuracy Meters': position.get('accuracyMeters'),
                'Altitude Meters': position.get('altitudeMeters'),
                'Source': position.get('source', ''),
                'Speed Meters/Second': position.get('speedMetersPerSecond', 0),
                'Segment Type': 'Position'
            }
            
            timeline_data.append(position_entry)
        
        # Process semantic segments
        semantic_segments = data.get('semanticSegments', [])
        print(f"\nFound {len(semantic_segments)} semantic segments")
        
        for segment in semantic_segments:
            start_time, start_offset = parse_datetime(segment.get('startTime'))
            end_time, end_offset = parse_datetime(segment.get('endTime'))
            
            # Process timeline paths
            timeline_paths = segment.get('timelinePath', [])
            for path in timeline_paths:
                point = path.get('point')
                path_time, path_time_offset = parse_datetime(path.get('time'))
                lat, lon = clean_and_parse_coordinates(point)
                
                path_entry = {
                    'Time': path_time or start_time,
                    'Time Offset': path_time_offset or start_offset,
                    'Start Time': start_time,
                    'Start Time Offset': start_offset,
                    'End Time': end_time,
                    'End Time Offset': end_offset,
                    'Point': str(point),
                    'Latitude': lat,
                    'Longitude': lon,
                    'Segment Type': 'Timeline Path'
                }
                timeline_data.append(path_entry)
            
            # Process visits
            visit = segment.get('visit')
            if visit:
                top_candidate = visit.get('topCandidate', {})
                visit_entry = {
                    'Time': start_time,
                    'Time Offset': start_offset,
                    'Start Time': start_time,
                    'Start Time Offset': start_offset,
                    'End Time': end_time,
                    'End Time Offset': end_offset,
                    'Segment Type': 'Visit',
                    'Hierarchy Level': visit.get('hierarchyLevel'),
                    'Visit Probability': visit.get('probability'),
                    'Place ID': top_candidate.get('placeId'),
                    'Semantic Type': top_candidate.get('semanticType'),
                    'Place Probability': top_candidate.get('probability'),
                    'Latitude': clean_and_parse_coordinates(top_candidate.get('placeLocation', {}).get('latLng'))[0],
                    'Longitude': clean_and_parse_coordinates(top_candidate.get('placeLocation', {}).get('latLng'))[1]
                }
                timeline_data.append(visit_entry)
            
            # Process activities
            activity = segment.get('activity')
            if activity:
                start_lat, start_lon = clean_and_parse_coordinates(activity.get('start', {}).get('latLng'))
                end_lat, end_lon = clean_and_parse_coordinates(activity.get('end', {}).get('latLng'))
                top_candidate = activity.get('topCandidate', {})
                
                activity_entry = {
                    'Time': start_time,
                    'Time Offset': start_offset,
                    'Start Time': start_time,
                    'Start Time Offset': start_offset,
                    'End Time': end_time,
                    'End Time Offset': end_offset,
                    'Segment Type': 'Activity',
                    'Start Latitude': start_lat,
                    'Start Longitude': start_lon,
                    'End Latitude': end_lat,
                    'End Longitude': end_lon,
                    'Distance Meters': activity.get('distanceMeters'),
                    'Activity Type': top_candidate.get('type'),
                    'Activity Probability': top_candidate.get('probability')
                }
                timeline_data.append(activity_entry)
        
        # Check if location data is empty
        if not timeline_data:
            print("Warning: No location data found to convert!")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(timeline_data)
        
        # Sort by time if time column exists
        if 'Time' in df.columns:
            df = df.sort_values('Time')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_file), exist_ok=True) if os.path.dirname(csv_file) else None
        
        # Save CSV
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"Conversion complete. CSV saved to {csv_file}")
        print(f"Number of rows in CSV: {len(df)}")
        
        # Print first few rows for verification
        print("\nFirst few rows of data:")
        print(df.head())
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

# Call the function with your specific paths
# Modify these paths as needed
convert_timeline_to_csv(
    r'C:\ENTER PATH FOR INPUT FILE\Timeline.json', 
    r'C:\ENTER PATH FOR OUTPUT FILE\Timeline.csv'
)
