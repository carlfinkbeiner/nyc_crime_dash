import json

with open('/Users/carlfinkbeiner/Riverside_Analytics/nyc_crime_dash/data/police_precincts.geojson') as f:
     nyc_precincts_geojson = json.load(f)




# Assuming the structure of your GeoJSON is consistent with the provided example
nyc_precincts_lookup = {feature['properties']['precinct']: feature for feature in nyc_precincts_geojson['features']}

# Testing the lookup with a known precinct number, for example, '1'
test_precinct = '1'
if test_precinct in nyc_precincts_lookup:
    print("Precinct found:", nyc_precincts_lookup[test_precinct])
else:
    print(f"Precinct {test_precinct} not found in lookup")
