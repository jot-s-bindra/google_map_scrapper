import csv
import json

def csv_to_json(csv_file, json_file):
    with open(csv_file, 'r') as file:
        csv_data = csv.DictReader(file)
        data = list(csv_data)

    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)


csv_to_json('google_maps_data.csv', 'output.json')
