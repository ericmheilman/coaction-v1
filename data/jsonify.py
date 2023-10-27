import json

# Initialize an empty list to hold the dictionaries
data = []

# Open the input file in read mode
with open('input.txt', 'r') as f:
    # Loop through each line in the file
    for line in f:
        # Split the line on whitespace
        address, value = line.split()
        # Add a dictionary to the data list
        data.append({"address": address, "value": float(value)})

# Open the output file in write mode
with open('output.json', 'w') as f:
    # Write the data to the file in JSON format
    json.dump(data, f, indent=4)

