import xml.etree.ElementTree as ET
import csv
import datetime
from collections import defaultdict
import pytz
import logging

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Map data from export.xml to workout names needed for logging a workout 
WORKOUT_TYPE_MAPPING = {
    "HKWorkoutActivityTypePilates": "Pilates",
    "HKWorkoutActivityTypeFunctionalStrengthTraining": "Pilates",
    "HKWorkoutActivityTypeWalking": "Walking",
    "HKWorkoutActivityTypeRunning": "Running",
    "HKWorkoutActivityTypeYoga": "Yoga",
    "HKWorkoutActivityTypeRowing": "Rowing",
    "HKWorkoutActivityTypeCrossCountrySkiing": "Cross Country Skiing",
    "HKWorkoutActivityTypeCycling": "Cycling",
    "HKWorkoutActivityTypeMartialArts": "Martial Arts",
    "HKWorkoutActivityTypeTraditionalStrengthTraining": "Pilates",
    "HKWorkoutActivityTypeFlexibility": "Pilates"
    # Add more mappings as needed
}

def parse_apple_health_export(xml_file):
    """
    Convert export.xml exported from Apple Heath and create a dictionary of each workout nested in a list called workouts
    """
    # Parse the XML file and create an ElementTree object (structure of Apple Health data)
    tree = ET.parse(xml_file)
    # Get the root element of the XML tree
    root = tree.getroot()

    workouts = []
    weight_measurements = []
    mets_sum = defaultdict(float)
    mets_count = defaultdict(int)

    # Collect all weight measurements from xml file
    for record in root.findall('.//Record'):
        if record.get('type') == 'HKQuantityTypeIdentifierBodyMass':
            weight_measurements.append({
                'date': datetime.datetime.strptime(record.get('startDate'), '%Y-%m-%d %H:%M:%S %z'),
                'value': float(record.get('value')),
                'unit': record.get('unit')
            })

    # Sort weight measurements by date
    weight_measurements.sort(key=lambda x: x['date'])

    # First pass: collect METs data
    for workout in root.findall('.//Workout'):
        workout_type = WORKOUT_TYPE_MAPPING.get(workout.get('workoutActivityType'), workout.get('workoutActivityType'))
        for metadata in workout.findall('.//MetadataEntry'):
            if metadata.get('key') == 'HKAverageMETs':
                mets_value = float(metadata.get('value').split()[0])
                if mets_value > 0:
                    mets_sum[workout_type] += mets_value
                    mets_count[workout_type] += 1

    # Calculate average METs for each workout type
    avg_mets = {wtype: mets_sum[wtype] / mets_count[wtype] if mets_count[wtype] > 0 else 0 for wtype in mets_sum}

    # Second pass: process workouts
    for workout in root.findall('.//Workout'):
        workout_type = workout.get('workoutActivityType')
        if workout_type not in WORKOUT_TYPE_MAPPING:
            print(f"Warning: No mapping found for workout type {workout_type}")
        
        workout_data = {
            'workoutActivityType': WORKOUT_TYPE_MAPPING.get(workout_type, workout_type),
            'duration': float(workout.get('duration', 0)),
            'distance': 0,  # Default distance
            'calories': 0.1, # ensure non-zero calories
            'startDate': ''
        }

        # Format start date
        if workout.get('startDate'):
            date_string = workout.get('startDate')
            try:
                date_obj = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S %z')
            except ValueError:
                date_obj = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            workout_data['startDate'] = date_obj.strftime('%Y-%m-%d %H:%M:%S')

        # Extract distance for running and walking workouts
        for stat in workout.findall('.//WorkoutStatistics'):
            if stat.get('type') == 'HKQuantityTypeIdentifierDistanceWalkingRunning':
                workout_data['distance'] = float(stat.get('sum', 0))

        # Find the most recent weight measurement before this workout
        workout_start = datetime.datetime.strptime(workout_data['startDate'], '%Y-%m-%d %H:%M:%S')
        workout_start = pytz.timezone('America/Regina').localize(workout_start)  # Assume Regina timezone, adjust if needed
        latest_weight = next((w for w in reversed(weight_measurements) if w['date'] <= workout_start), None)
        
        weight = latest_weight['value'] if latest_weight else 71.2  # Default weight if no measurement found

        # Extract HKAverageMETs
        mets = 0
        for metadata in workout.findall('.//MetadataEntry'):
            if metadata.get('key') == 'HKAverageMETs':
                mets = float(metadata.get('value').split()[0])
                break
        
        # if mets has no value, assign it the average of all the other mets values for that activity
        if mets == 0:
            mets = avg_mets.get(workout_data['workoutActivityType'], 0)
        
        # calculate calories
        # equation modified from https://blog.nasm.org/metabolic-equivalents-for-weight-loss
        if mets > 0:
            workout_data['calories'] = round((3.5 * workout_data['duration'] * mets * weight) / 200)
        
        workouts.append(workout_data)

    return workouts

def write_to_csv(data, filename):
    """
    write data to a csv file using only the categories of 'workoutActivityType', 'duration', 'distance', 'calories', 'startDate'
    """
    keys = ['workoutActivityType', 'duration', 'distance', 'calories', 'startDate']
    with open(filename, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)

def main():
    xml_file = 'export.xml'  # Replace with your XML file path
    workouts = parse_apple_health_export(xml_file)

    # Sort workouts by start date
    workouts.sort(key=lambda x: datetime.datetime.strptime(x['startDate'], '%Y-%m-%d %H:%M:%S'))

    write_to_csv(workouts, 'workouts_with_mets_and_weight.csv')
    print(f"Exported {len(workouts)} workouts to workouts_with_mets_and_weight.csv")

if __name__ == "__main__":
    main()