from math import hypot
from operator import itemgetter

import plotly.plotly as py

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
    :param jobs: Jobs with degree requirement information
    :param city_coords: Dict of city names to their gps coordinates
    :param include_others: Boolean to include jobs that aren't near cities as their own category
    :return:
    """
    degree_city_counts = {}
    city_totals = {city: 0 for city in list(city_coords.keys()) + ['others']}

    # Get a count of degrees per city and total number of jobs in each city
    for job in jobs:
        degree_class = job['degree_classification']
        closest_city = _find_closest_city(city_coords, (job['latitude'], job['longitude']))
        if include_others and not closest_city:
            closest_city = 'others'
        if closest_city:
            if degree_class not in degree_city_counts:
                degree_city_counts[degree_class] = {city: 0 for city in city_coords.keys()}
                if include_others:
                    degree_city_counts[degree_class]['others'] = 0

            degree_city_counts[degree_class][closest_city] += 1
            city_totals[closest_city] += 1

    # The order to show the degrees in the bar chart from left to right
    ordered_degrees = ['undergrad', 'ms', 'ms/phd', 'phd', 'unknown']
    # Sort the bar graph from most to least number of jobs from top to bottom
    sorted_cities = [city for city, count in sorted(city_totals.items(), key=itemgetter(1))]

    # Create figure for the bar graph
    fig = []
    for degree in ordered_degrees:
        counts = []
        cities = []
        for city in sorted_cities:
            counts.append(degree_city_counts[degree][city])
            cities.append(city)

        fig.append({
            'x': counts,
            'y': cities,
            'name': degree,
            'orientation': 'h',
            'marker': {'color': DEGREE_COLORS[degree]},
            'type': 'bar'})
    py.plot({'data': fig, 'layout': {'barmode': 'stack'}})


def plot_degree_map(jobs):
    """
    Plot the degrees on a map of the United States
    :param jobs: Jobs with degree requirement information
    :return:
    """
    degrees = {}
    plot_data = []
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

    for job in jobs:
        degree_class = job['degree_classification']

        if degree_class not in degrees:
            degrees[degree_class] = {
                'longitude': [],
                'latitude': [],
                'jobtitle': []}
        degrees[degree_class]['longitude'].append(job['longitude'])
        degrees[degree_class]['latitude'].append(job['latitude'])
        degrees[degree_class]['jobtitle'].append(job['jobtitle'])

    for degree, data in degrees.items():
        plot_data.append({
            'name': degree,
            'type': 'scattergeo',
            'locationmode': 'USA-states',
            'lon': data['longitude'],
            'lat': data['latitude'],
            'text': data['jobtitle'],
            'marker': {'color': DEGREE_COLORS[degree]}})

    fig = {'data': plot_data, 'layout': layout}
    py.plot(fig, filename='job-degree-requirements')


def plot_jobs_not_in_city_for_degree_requierments(jobs, city_coords):
    """
    Plot jobs that are not near <city_coords>
    :param jobs: Jobs with degree requirement information
    :param city_coords: Dict of city names to their gps coordinates
    :return:
    """
    degree_jobs = {}
    plot_data = []
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

    for job in jobs:
        if not _find_closest_city(city_coords, (job['latitude'], job['longitude'])):
            degree_class = job['degree_classification']
            if degree_class not in degree_jobs:
                degree_jobs[degree_class] = []
            degree_jobs[degree_class].append(job)

    for degree, deg_jobs in degree_jobs.items():
        latitudes = []
        longitudes = []
        for job in deg_jobs:
            latitudes.append(job['latitude'])
            longitudes.append(job['longitude'])

        plot_data.append({
            'name': degree,
            'type': 'scattergeo',
            'locationmode': 'USA-states',
            'lat': latitudes,
            'lon': longitudes,
            'marker': {'color': DEGREE_COLORS[degree]}})

    fig = {'data': plot_data, 'layout': layout}
    py.plot(fig, filename='city-job-degree-requirements')
