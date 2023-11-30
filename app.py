import dash
import requests
from dash import html, dcc, Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import json
import time


# arrest_data_url = 'https://raw.githubusercontent.com/carlfinkbeiner/nyc_crime_dash/main/data/arrest_data_processed.csv'
# precinct_geojson_url = 'https://github.com/carlfinkbeiner/nyc_crime_dash/blob/main/data/police_precincts.geojson'

arrest_data = pd.read_csv('data/arrest_data_processed.csv')

with open('/Users/carlfinkbeiner/nyc_crime_dash/data/police_precincts.geojson') as f:
     nyc_precincts_geojson = json.load(f)


borough_colors = {
    "Manhattan": "#db1f48",
    "Brooklyn": "#C3B678",
    "Queens": "#01949a",
    "Bronx": "#a65628",
    "Staten Island": "#8D82B6"
}

custom_background_color = '#333333'
#https://dash-example-index.herokuapp.com/cheatsheet

# Aggregating total arrests per year and precinct
arrests_year_precinct = arrest_data.groupby(['year', 'ARREST_PRECINCT']).sum()['arrest_count'].reset_index()
arrests_year_precinct_crime = arrest_data.groupby(['year','ARREST_PRECINCT','OFNS_DESC']).sum()['arrest_count'].reset_index()
arrests_year_boro = arrest_data.groupby(['year','ARREST_BORO']).sum()['arrest_count'].reset_index()
arrests_year_boro_crime = arrest_data.groupby(['year','ARREST_BORO','OFNS_DESC']).sum()['arrest_count'].reset_index()
arrests_month_boro = arrest_data.groupby(['month','ARREST_BORO']).sum()['arrest_count'].reset_index()
arrests_month_boro_crime_precinct = arrest_data.groupby(['month','ARREST_BORO','OFNS_DESC','ARREST_PRECINCT']).sum()['arrest_count'].reset_index()
arrests_year_boro_crime_precinct = arrest_data.groupby(['year','ARREST_BORO','OFNS_DESC','ARREST_PRECINCT']).sum()['arrest_count'].reset_index()


# Initialize the Dash application
app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.Div([
            html.H1("Crime in New York City", className='header-title')
            ], className='header-left'
        ),
        html.Div([
            html.A([
                html.Img(src='/assets/ra_white.png', className='logo')
                ], href='https://www.riverside-analytics.com/', target='_blank')
            ], className='header-right'
        ),
        html.Div([
            html.A([
                html.Img(src='assets/plotly_white.png', className='logo')
                ], href='https://dash.plotly.com/', target='_blank')
            ], className='header-right'
        ),
        ],
        className='dashboard-header'
    ),
    #content container
    html.Div([
        # Side panel for dropdowns and toggles  
        html.Div([
            html.Div(
                dcc.Markdown("""
                    This dashboard is designed to allow a user to explore crime trends in New York City. Arrest data is sourced from the NYS Open Data Program and covers all years from 2006 to 2022. This dataset is updated annually and was initially released to the public in 2018 to offer greater insight into police enforcement activity.
                    """),
                className='static-text-box'
            ),
            html.Label("Map Type:", className='dropdown-label',style={'color': '#FFFFFF'}),
            # Toggles for the map type
            dcc.RadioItems(
                id='map-toggle',
                options=[
                    {'label': 'Total Arrests', 'value': 'total_arrests'},
                    {'label': 'Percent Change', 'value': 'percent_change'}
                ],
                value='total_arrests',  # default value
                labelStyle={'display': 'inline-block'},
                className='radio-items'
            ),

            #Crime selection dropdown
            html.Label("Select Crime:", className='dropdown-label',style={'color': '#FFFFFF'}),
            dcc.Dropdown(
                id='crime-type-dropdown',
                options=[{'label': crime, 'value': crime} for crime in arrests_year_precinct_crime['OFNS_DESC'].unique()],
                value=None,
                multi=True,                
                className='dropdown'
            ),
            
            # Year and crime type dropdowns for 'Percent Change' map
            html.Div(id='percent-change-controls', children=[
                html.Label("Select Year 1:", className='dropdown-label',style={'color': '#FFFFFF'}),
                dcc.Dropdown(
                    id='year1-dropdown',
                    options=[{'label': year, 'value': year} for year in arrests_year_precinct['year'].unique()],
                    value=((arrests_year_precinct['year'].max())-1),
                    className='dropdown'
                ),
                html.Label("Select Year 2:", className='dropdown-label',style={'color': '#FFFFFF'}),
                dcc.Dropdown(
                    id='year2-dropdown',
                    options=[{'label': year, 'value': year} for year in arrests_year_precinct['year'].unique()],
                    value=arrests_year_precinct['year'].max(),
                    className='dropdown'
                ),

            ], style={'display': 'none'}),  # This div is hidden by default
            
            # Year dropdown for 'Total Arrests' map
            html.Div(id='total-arrests-controls', children=[
                html.Label("Select Year:", className='dropdown-label',style={'color': '#FFFFFF'}),
                dcc.Dropdown(
                    id='arrest-year-dropdown',
                    options=[{'label': year, 'value': year} for year in arrests_year_precinct['year'].unique()],
                    value=arrests_year_precinct['year'].max(),
                    className='dropdown'
                ),
            ]),
            html.Button('Reset Dashboard', id='reset-button', n_clicks=0, className='reset-button')

            
        ], className='side-panel'),
         # Main panel for maps and charts
        html.Div([
            # Maps will be displayed here based on the toggle selection
            dcc.Loading(
                id="loading_maps",
                type="default",
                children=
                    html.Div([
                        html.Div(dcc.Graph(id='crime-change-map', className='map-graph'), id='percent-change-map-container', style={'display': 'none'}),  # initially hidden
                        html.Div(dcc.Graph(id='arrest-map', className='map-graph'), id='total-arrests-map-container')  # initially visible
                        ], id='map-container')
            ),
            
            # Bar charts container
            html.Div([
                dcc.Loading(
                    id="loading-boro-crime-bar",
                    type="default",
                    children=html.Div(dcc.Graph(id='boro-crime-bar', className='bar-graph'))
                ),
                dcc.Loading(
                    id="loading-month-crime-bar",
                    type="default",
                    children=html.Div(dcc.Graph(id='month-crime-bar', className='bar-graph'))
                ),
                dcc.Loading(
                    id="loading-precinct-crime-bar",
                    type="default",
                    children=html.Div(dcc.Graph(id='precinct-crime-bar', className='bar-graph'))
                )
                ], className='charts-container')    
        ], className='main-panel')
    ], className='content-container'),
    html.Div(id='hidden-div', style={'display': 'none'}),
    html.Div(id='dummy-div', children='constant', style={'display': 'none'})
], className='dashboard-container')



# Toggle options callback
@app.callback(
    [Output('percent-change-controls', 'style'),
     Output('total-arrests-controls', 'style')],
    [Input('map-toggle', 'value')]
)
def toggle_map_controls(selected_map):
    if selected_map == 'total_arrests':
        return {'display': 'none'}, {'display': 'block'}
    elif selected_map == 'percent_change':
        return {'display': 'block'}, {'display': 'none'}
    


#Map toggle callback
@app.callback(
    [Output('percent-change-map-container', 'style'),
     Output('total-arrests-map-container', 'style')],
    [Input('map-toggle', 'value')]
)
def toggle_map(selected_map):
    if selected_map == 'percent_change':
        return {'display': 'block'}, {'display': 'none'}
    elif selected_map == 'total_arrests':
        return {'display': 'none'}, {'display': 'block'}
    else:
        # If for some reason the selected_map is neither, hide both
        return {'display': 'none'}, {'display': 'none'}


#Reset button callback
@app.callback(
    Output('hidden-div', 'children'),
    [Input('reset-button', 'n_clicks'),
     Input('arrest-map', 'clickData')],
    [State('hidden-div', 'children')]
)
def update_view(reset_clicks, clickData, hidden_div_state):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'reset-button':
        return None  # Clear the selection
    elif trigger_id == 'arrest-map':
        if clickData:
            return clickData['points'][0]['location']  # Update selection based on map click
        return hidden_div_state

    return hidden_div_state


#Reset crime dropdown
@app.callback(
       Output('crime-type-dropdown','value'),
       [Input('reset-button','n_clicks')],
       [State('crime-type-dropdown','value')]
)
def update_dropdown(reset_clicks,dropdown_state):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'reset-button':
        return None
    else:
        return dropdown_state

# Percent change arrest map
@app.callback(
    Output('crime-change-map', 'figure'),
    [Input('year1-dropdown', 'value'),
     Input('year2-dropdown', 'value'),
     Input('crime-type-dropdown', 'value'),
     Input('map-toggle', 'value')]
)
def update_percent_change_map(year1, year2, crime_types, selected_map):

    #Do not update if total arrest map selected
    if selected_map != 'percent_change':
        return dash.no_update  # Don't update this graph unless it's selected

    # Filter data for the selected years
    data_year1 = arrests_year_precinct[arrests_year_precinct['year'] == year1]
    data_year2 = arrests_year_precinct[arrests_year_precinct['year'] == year2]

    # If crime types are selected, filter the data further
    if crime_types:
        data_year1 = arrests_year_precinct_crime[(arrests_year_precinct_crime['year'] == year1) & 
                                                    (arrests_year_precinct_crime['OFNS_DESC'].isin(crime_types))]
        data_year2 = arrests_year_precinct_crime[(arrests_year_precinct_crime['year'] == year2) & 
                                                    (arrests_year_precinct_crime['OFNS_DESC'].isin(crime_types))]
        # Group by precinct to get total arrests for selected crime types
        data_year1 = data_year1.groupby('ARREST_PRECINCT').sum().reset_index()
        data_year2 = data_year2.groupby('ARREST_PRECINCT').sum().reset_index()


    # Merging the datasets to calculate percent change and include arrest counts
    merged_data = data_year1.merge(data_year2, on='ARREST_PRECINCT', suffixes=('_year1', '_year2'), how='outer')

    merged_data['percent_change'] = ((merged_data['arrest_count_year2'] - merged_data['arrest_count_year1']) / 
                                      merged_data['arrest_count_year1']) * 100

    # Creating the choropleth map with custom hover data
    fig = px.choropleth_mapbox(merged_data, 
                               geojson=nyc_precincts_geojson, 
                               locations='ARREST_PRECINCT', 
                               featureidkey="properties.precinct",
                               color='percent_change',
                               color_continuous_scale="Viridis",
                               range_color=(-100, 100),
                               mapbox_style="carto-darkmatter",
                               zoom=10, 
                               center = {"lat": 40.7128, "lon": -74.0060},
                               opacity=0.5,
                               labels={'percent_change': 'Percent Change in Arrests',
                                       'ARREST_PRECINCT': 'Precinct',
                                       'arrest_count_year1': 'Year 1 Arrests',
                                       'arrest_count_year2': 'Year 2 Arrests'},
                                hover_data={
                                'ARREST_PRECINCT': True,  # False to not repeat the precinct number
                                'percent_change': ':.2f',  # Format the percent change to 2 decimal places
                                'arrest_count_year1': f":.0f Arrests in {year1}f",  # Format arrest count for year1
                                'arrest_count_year2': f":.0f Arrests in {year2}"}
                              )


    #fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    fig.update_layout(
        legend=dict(
            title=None,  # Removes the title
            orientation='h',
            yanchor='bottom',
            y=0.5,  # Adjust this to move the legend up or down on the map
            xanchor='right',
            x=0.95,  # Adjust this to move the legend left or right on the map
            ),
        font=dict(
            size=13,
            color="white"
            ),
        legend_traceorder='reversed',
        margin=dict(l=0, r=0, t=0, b=0),  # Adjust margins to fit the legend inside the map area
        title='Precent Change in Arrests',
        title_x=0.027,
        title_y=0.95,
        legend_title=None,
        font_family="Helvetica"
    )

    # Customize the color bar
    fig.update_coloraxes(colorbar=dict(
        thickness=20,  # Controls the thickness of the color bar
        len=0.3,  # Controls the length of the color bar (percentage of the figure height)
        yanchor='bottom',
        y=0.5,  # Adjust this to move the color bar up or down
        xanchor='right',
        x=0.95  # Adjust this to move the color bar left or right
    ))

    return fig





nyc_precincts_lookup = {feature['properties']['precinct']: feature for feature in nyc_precincts_geojson['features']}

def get_highlights(selected_precinct, precinct_lookup=nyc_precincts_lookup):
    geojson_highlights = {'type': 'FeatureCollection', 'features': []}
    target = str(selected_precinct)

    if target in precinct_lookup:
        geojson_highlights['features'].append(precinct_lookup[target])
    return geojson_highlights



#Arrest count map
@app.callback(
    Output('arrest-map', 'figure'),
    [Input('arrest-year-dropdown', 'value'),
     Input('crime-type-dropdown', 'value'),
     Input('map-toggle', 'value'),
     Input('hidden-div','children')]

)
def update_arrest_map(year, crime_types,selected_map,selected_precinct):

    #Do not update if total_arrests not selected
    if selected_map != 'total_arrests':
        return dash.no_update  # Don't update this graph unless it's selected

    
    # Filter data for the selected years
    data_filtered = arrests_year_precinct[arrests_year_precinct['year'] == year]


    # If crime types are selected, filter the data further
    if crime_types:
        data_filtered = arrests_year_precinct_crime[(arrests_year_precinct_crime['year'] == year) & 
                                                (arrests_year_precinct_crime['OFNS_DESC'].isin(crime_types))]

        # Group by precinct to get total arrests for selected crime types
        data_filtered = data_filtered.groupby('ARREST_PRECINCT').sum().reset_index()


    data_filtered = data_filtered.groupby('ARREST_PRECINCT').sum().reset_index()


    # Creating the choropleth map with custom hover data
    fig = px.choropleth_mapbox(data_filtered, 
                               geojson=nyc_precincts_geojson, 
                               locations='ARREST_PRECINCT', 
                               featureidkey="properties.precinct",
                               color='arrest_count',
                               color_continuous_scale="Viridis",
                               range_color=(data_filtered['arrest_count'].min(), data_filtered['arrest_count'].max()),
                               mapbox_style="carto-darkmatter",
                               zoom=10, 
                               center = {"lat": 40.7128, "lon": -74.0060},
                               opacity=0.5,
                                labels={
                                        'ARREST_PRECINCT': 'Precinct',
                                        'arrest_count': 'Arrest Count'
                                        }
    )           


    fig = fig.update_layout(
        legend=dict(
            title_text="",  # Removes the title
            orientation='h',
            yanchor='bottom',
            y=0.5,  # Adjust this to move the legend up or down on the map
            xanchor='right',
            x=0.95,  # Adjust this to move the legend left or right on the map
            ),
        font=dict(
            size=13,
            color="white"
            ),
        legend_traceorder='reversed',
        margin=dict(l=0, r=0, t=0, b=0),  # Adjust margins to fit the legend inside the map area,
        title=f'Arrests in {year}',
        title_x=0.027,
        title_y=0.95,
        legend_title="",
        font_family="Helvetica"
    )

    # Customize the color bar
    fig.update_coloraxes(colorbar=dict(
        thickness=20,  # Controls the thickness of the color bar
        len=0.3,  # Controls the length of the color bar (percentage of the figure height)
        yanchor='bottom',
        y=0.5,  # Adjust this to move the color bar up or down
        xanchor='right',
        x=0.95  # Adjust this to move the color bar left or right
    ))

    if selected_precinct is not None:

        highlights = get_highlights(selected_precinct)

        fig.add_trace(
        px.choropleth_mapbox(data_filtered, geojson=highlights, 
                             color="arrest_count",
                             locations="ARREST_PRECINCT", 
                             featureidkey="properties.precinct",                                 
                             opacity=1).data[0]
    )

    return fig



#Arrest count bar
@app.callback(
    Output(component_id='boro-crime-bar',component_property='figure'),
    [Input(component_id='crime-type-dropdown',component_property='value'),
    Input(component_id='hidden-div',component_property='children'),
    Input(component_id='dummy-div',component_property='children')]
)
def update_bar(crime_types,selected_precinct,dummy_value):

    boro_arrests = arrests_year_boro_crime_precinct

    if crime_types:
        boro_arrests = boro_arrests[(boro_arrests['OFNS_DESC'].isin(crime_types))]
    
    if selected_precinct:
        boro_arrests = boro_arrests[(boro_arrests['ARREST_PRECINCT'] == selected_precinct)]


    arrest_data = boro_arrests.groupby(['year','ARREST_BORO']).sum().reset_index()

    if selected_precinct is None and crime_types is None:
        title = 'Yearly Arrests'
    
    elif selected_precinct is not None and crime_types is not None:
        title = f'Yearly Arrests in Precinct {selected_precinct} (filtered by crime)'
    
    elif selected_precinct:
        title = f'Yearly Arrests in Precinct {selected_precinct}'
    
    elif crime_types:
        title = 'Yearly Arrests (filtered by crime)'
    
    else:
        title = 'Yearly Arrests'
    
    time.sleep(1)

    arrest_bar = px.bar(arrest_data, 
            x='year', 
            y='arrest_count', 
            color='ARREST_BORO',
            title=title,
            labels={
                'year': 'Year',
                'arrest_count': 'Arrest count',
                'ARREST_BORO': 'Borough'
            },
            color_discrete_map=borough_colors
    )
    
    arrest_bar.update_layout({
            'plot_bgcolor': custom_background_color,
            'paper_bgcolor': custom_background_color,
            'font_color': 'white'
            },
            legend_title_text='',
            showlegend=False,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,  # Slightly above the top
                xanchor='center',
                x=0.5
            ),
            template='plotly',
            margin=dict(t=60),
            title={
                'text': title,
                'y':0.95,  # Adjusts the title's vertical position. You may not need this if `t=60` works well.
                'x':0.1,  # Centers the title
                'xanchor': 'left',
                'yanchor': 'top'
            },
            title_pad=dict(t=1),
            font_family="Helvetica"  # Adjust the padding to give the title some space if needed           
    )

    return arrest_bar



#Monthly arrest bar
@app.callback(
    Output(component_id='month-crime-bar', component_property='figure'),
    [Input(component_id='crime-type-dropdown', component_property='value'),
     Input(component_id='hidden-div', component_property='children'),
     Input(component_id='arrest-year-dropdown', component_property='value')]
)
def update_monthly_bar(crime_types, selected_precinct, year):
    # Initial data filtering based on selected_precinct
    if selected_precinct:
        filtered_data = arrest_data[arrest_data['ARREST_PRECINCT'] == selected_precinct]
    else:
        filtered_data = arrest_data

    # Filtering based on crime_types
    if crime_types:
        filtered_data = filtered_data[filtered_data['OFNS_DESC'].isin(crime_types)]
    # No else needed here, if crime_types is None or empty, filtered_data remains as is

    # Filtering based on year
    if year:
        filtered_data = filtered_data[filtered_data['year'] == year]
    # No else needed here as well, if year is None, filtered_data remains as is

    # Group by month and BORO
    arrests_grouped = filtered_data.groupby(['month', 'ARREST_BORO']).sum()['arrest_count'].reset_index()

    #Getting title
    if selected_precinct is None and crime_types is None and year is None:
        title = 'Monthly Arrests'
    
    elif selected_precinct is not None and crime_types is not None and year is not None:
        title = f'Monthly Arrests in Precinct {selected_precinct} in {year} (filtered by crime)'
    
    elif selected_precinct is not None and year is not None:
        title = f'Monthly Arrests in Precinct {selected_precinct} in {year}'
    
    elif year is not None:
        title = f'Monthly Arrests in {year}'
    
    elif crime_types is not None and year is not None:
        title = f'Monthly Arrests in {year}(filtered by crime)'
    
    else:
        title = 'Monthly Arrests'
        


    months_ordered = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    arrests_grouped['month'] = pd.Categorical(arrests_grouped['month'], categories=months_ordered, ordered=True)

    arrests_grouped = arrests_grouped.sort_values('month')
    
    time.sleep(1)

    monthly_bar = px.line(
        arrests_grouped,
        x='month',
        y='arrest_count', color='ARREST_BORO',
        title=title,
        labels={
            'month': 'Month',
            'arrest_count': 'Arrest Count',
            'ARREST_BORO': 'Borough'
         },
         color_discrete_map=borough_colors
    )

    monthly_bar.update_layout({
        'plot_bgcolor': custom_background_color,
        'paper_bgcolor': custom_background_color,
        'font_color': 'white'
        }, 
        legend_title_text='',
        showlegend=False,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,  # Slightly above the top
            xanchor='center',
            x=0.5
        ),
        title={
            'text': title,
            'y':0.95,  # Adjusts the title's vertical position. You may not need this if `t=60` works well.
            'x':0.1,  # Centers the title
            'xanchor': 'left',
            'yanchor': 'top'
        },
        title_pad=dict(t=1),  # Adjust the padding to give the title some space if needed 
        margin=dict(t=60),
        font_family="Helvetica"
    )
    
    monthly_bar.update_traces(line=dict(width=3))

    return monthly_bar



#Precinct crime bar
@app.callback(
    Output('precinct-crime-bar', 'figure'),
    [Input('arrest-year-dropdown', 'value'),
     Input('hidden-div','children')]
)
def update_precinct_bar(year, selected_precinct):

    if selected_precinct is None:
        filtered_data = arrests_year_precinct_crime[arrests_year_precinct_crime['year'] == year]

    else:
        filtered_data = arrests_year_precinct_crime[(arrests_year_precinct_crime['year'] == year) & (arrests_year_precinct_crime['ARREST_PRECINCT'] == selected_precinct)]
    

    #data_filtered = filtered_data.sort_values('arrest_count', ascending=False)
    data_filtered = filtered_data.groupby(['OFNS_DESC']).sum()['arrest_count'].reset_index()
    data_filtered = data_filtered.sort_values('arrest_count', ascending=False)
    top_10 = data_filtered.head(10).sort_values('arrest_count', ascending=True)

        #Getting title
    if selected_precinct is None and year is None:
        title = 'Arrest Types'
    
    elif selected_precinct is not None and year is not None:
        title = f'Arrest Types in Precinct {selected_precinct} in {year}'
    
    elif selected_precinct:
        title = f'Arrest Types in Precinct {selected_precinct}'
    
    elif year:
        title = f'Arrest Types in {year}'
    
    else:
        title = 'Arrest Types'




    time.sleep(1)
    bar = px.bar(
        top_10, 
        x='arrest_count', 
        y='OFNS_DESC', 
        orientation='h',
        title=title,
        labels={
            'OFNS_DESC': 'Offense',
            'arrest_count': 'Arrest count'
            }
    )
    
    fig = bar.update_layout({
                    'plot_bgcolor': custom_background_color,
                    'paper_bgcolor': custom_background_color,
                    'font_color': 'white'
                    },
                    template='plotly',
                    title={
                        'text': title,
                        'y':0.95,  # Adjusts the title's vertical position. You may not need this if `t=60` works well.
                        'x':0.1,  # Centers the title
                        'xanchor': 'left',
                        'yanchor': 'top'
                    },
                    title_pad=dict(t=1),  # Adjust the padding to give the title some space if needed 
                    font_family="Helvetica"
                )

    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)