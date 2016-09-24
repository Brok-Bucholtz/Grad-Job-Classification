from math import hypot
import plotly.plotly as py
import pandas as pd

DEGREE_COLORS = {
    'unknown': 'lightgreen',
    'ms/phd': 'gold',
    'phd': 'coral',
    'ms': 'royalblue',
    'undergrad': 'sienna'}


def _find_closest_city(cities, coord, max_distance=1):
    closest_city = None
    closest_distance = None
    for city, city_coord in cities.items():
        distance = hypot(city_coord[0] - coord[0], city_coord[1] - coord[1])
        if distance < max_distance and (not closest_distance or distance < closest_distance):
            closest_city = city
            closest_distance = distance

    return closest_city


def plot_degree_count_city_bar_chart(jobs, city_coords, include_others=False):
    """
    Plot a bar chart of all job degree requierments for cities
    :param jobs: Dataframe with degree requirement information
    :param city_coords: Dict of city names to their gps coordinates
    :param include_others: Boolean to include jobs that aren't near cities as their own category
    :return:
    """
    degree_city = pd.DataFrame()
    degree_city['degree_classification'] = jobs['degree_classification']

    # Find the closest city to all job gps coordinates
    degree_city['closest_city'] =\
        jobs[['latitude', 'longitude']]\
            .apply(lambda row: _find_closest_city(city_coords, row), axis=1)
    if include_others:
        degree_city['closest_city'] = degree_city['closest_city'].fillna('others')

    # Get the total number of jobs for each city
    degree_city['total'] = degree_city.groupby(['closest_city'])['degree_classification'].transform('count')

    # Get the number of degrees per city per degree
    degree_city_counts = degree_city.groupby(['degree_classification', 'closest_city']).size()
    degree_city = degree_city.drop_duplicates().set_index(['degree_classification', 'closest_city'])
    degree_city['count'] = degree_city_counts

    # The order to show the degrees in the bar chart from left to right
    ordered_degrees = [
        degree for degree in ['undergrad', 'ms', 'ms/phd', 'phd', 'unknown'] if degree in degree_city['count']]
    # Sort the bar graph from most to least number of jobs from top to bottom
    degree_city = degree_city.sort_values('total')

    # Prepare the data for the bar graph
    plt_data = []
    for degree in ordered_degrees:
        plt_data.append({
            'x': degree_city['count'][degree].index,
            'y': degree_city['count'][degree],
            'name': degree,
            'orientation': 'v',
            'marker': {'color': DEGREE_COLORS[degree]},
            'type': 'bar'})
    py.plot({'data': plt_data, 'layout': {'barmode': 'stack'}})


def plot_degree_map(jobs):
    """
    Plot the degrees on a map of the United States
    :param jobs: Dataframe with degree requirement information
    :return:
    """
    layout = {
        'title': 'Job Degree Requierments',
        'showlegend': True,
        'geo': {
            'scope': 'usa',
            'projection': {'type': 'albers usa'},
            'showland': True,
            'showlakes': True,
            'landcolor': 'rgb(212, 212, 212)',
            'subunitcolor': 'rgb(255, 255, 255)',
            'countrycolor': 'rgb(255, 255, 255)',
            'lakecolor': 'rgb(255, 255, 255)'}}

    # Prepare data for the map
    plot_data = []
    for degree, data in jobs.groupby('degree_classification'):
        plot_data.append({
            'name': degree,
            'type': 'scattergeo',
            'locationmode': 'USA-states',
            'lon': data['longitude'],
            'lat': data['latitude'],
            'text': data['jobtitle'],
            'marker': {'color': DEGREE_COLORS[degree]}})

    py.plot({'data': plot_data, 'layout': layout})


def plot_jobs_not_in_city_for_degree_requierments(jobs, city_coords):
    """
    Plot jobs that are not near <city_coords>
    :param jobs: Dataframe with degree requirement information
    :param city_coords: Dict of city names to their gps coordinates
    :return:
    """
    layout = {
        'title': 'Job Degree Requierments',
        'showlegend': True,
        'geo': {
            'scope': 'usa',
            'projection': {'type': 'albers usa'},
            'showland': True,
            'showlakes': True,
            'landcolor': 'rgb(212, 212, 212)',
            'subunitcolor': 'rgb(255, 255, 255)',
            'countrycolor': 'rgb(255, 255, 255)',
            'lakecolor': 'rgb(255, 255, 255)'}}

    # Drop jobs that are not with in a city
    noncity_jobs = jobs[
        jobs[['latitude', 'longitude']].apply(lambda row: not _find_closest_city(city_coords, row), axis=1)]

    # Prepare data for the map
    plot_data = []
    for degree, job in noncity_jobs.groupby('degree_classification'):
        plot_data.append({
            'name': degree,
            'type': 'scattergeo',
            'locationmode': 'USA-states',
            'lat': job['latitude'],
            'lon': job['longitude'],
            'marker': {'color': DEGREE_COLORS[degree]}})

    py.plot({'data': plot_data, 'layout': layout})
