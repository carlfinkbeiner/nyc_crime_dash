import pandas as pd

# Define the path to your CSV file
file_path = '/Users/carlfinkbeiner/Riverside_Analytics/ny_crime/data/NYPD_Arrests_Data__Historic__20231119.csv'


# Load the data
df = pd.read_csv(file_path)

# Check the first few rows
print(df.head())


# Drop rows where crucial data is missing
df = df.dropna(subset=['ARREST_PRECINCT', 'ARREST_DATE'])

# Convert 'arrest_date' to datetime
df['ARREST_DATE'] = pd.to_datetime(df['ARREST_DATE'], errors='coerce')

# Handle errors or impossible dates
df = df.dropna(subset=['ARREST_DATE'])

# Extract the year from the 'arrest_date'
df['year'] = df['ARREST_DATE'].dt.year

df['month'] = df['ARREST_DATE'].dt.month

#Update boroughs
borough_mapping = {'M': 'Manhattan', 'Q': 'Queens', 'B': 'Bronx', 'S': 'Staten Island', 'K': 'Brooklyn'}
df['ARREST_BORO'] = df['ARREST_BORO'].replace(borough_mapping)


# Group by year and precinct, then count the number of arrests
arrests_per_year_precinct = df.groupby(['month','year','ARREST_PRECINCT','ARREST_BORO','OFNS_DESC']).size().reset_index(name='arrest_count')

#Update month names
month_mapping = {
    1: 'January', 
    2: 'February', 
    3: 'March', 
    4: 'April', 
    5: 'May',
    6: 'June', 
    7: 'July', 
    8: 'August', 
    9: 'September', 
    10: 'October',
    11: 'November', 
    12: 'December'  
    }

arrests_per_year_precinct['month'] = arrests_per_year_precinct['month'].replace(month_mapping)

print(arrests_per_year_precinct.head())

arrests_per_year_precinct.to_csv('arrest_data_processed.csv')












