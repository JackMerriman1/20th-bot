import json


with open("service_record_data.json", 'r') as f:
    jsn = json.load(f)

print(json.dumps(jsn, indent = 2))