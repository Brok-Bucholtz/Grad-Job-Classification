from math import floor, ceil, sqrt, hypot

import matplotlib.pyplot as plt
import plotly.plotly as py

from feature_extraction import degree_classification, is_machine_learning_title


def _find_closest_city(cities, coord, max_distance=1):
    closest_city = None
    closest_distance = None
    for city, city_coord in cities.items():
        distance = hypot(city_coord[0] - coord[0], city_coord[1] - coord[1])
        if distance < max_distance and (not closest_distance or distance < closest_distance):
            closest_city = city
            closest_distance = distance

    return closest_city


def plot_degree_count_city_piechart(database, job_title, city_coords):
    """
    Plot pie charts showing the number of degrees per top locations
    :param database: Database with the job data
    :param job_title: Job title to analyse
    :return:
    """
    city_degree_counts = {}
    fig = plt.figure()
    for job in database.jobs.find({'search_title': job_title, 'finished_processing': True}):
        # ToDo: Replace is_machine_learning_title with a prediction model that applys to all jobs
        if job_title != 'machine learning' or is_machine_learning_title(job['jobtitle']):
            closest_city = _find_closest_city(city_coords, (job['latitude'], job['longitude']))
            if closest_city:
                if closest_city not in city_degree_counts:
                    city_degree_counts[closest_city] = {
                        'unknown': 0,
                        'undergrad': 0,
                        'ms/phd': 0,
                        'ms': 0,
                        'phd': 0}
                city_degree_counts[closest_city][degree_classification(database, job)] += 1

    # Create pie charts
    colors = ['lightgreen', 'gold', 'coral', 'royalblue', 'sienna']
    for city_i, (city, degree_counts) in enumerate(city_degree_counts.items()):
        labels = []
        sizes = []
        total = sum([count for degree, count in degree_counts.items()])
        for degree, degree_count in degree_counts.items():
            labels.append(degree)
            sizes.append(degree_count/total)

        location_plt = fig.add_subplot(floor(sqrt(len(city_degree_counts))), ceil(sqrt(len(city_degree_counts))), city_i+1)
        location_plt.set_title('{} - {}'.format(city, total))
        location_plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
    plt.show()


def plot_degree_map(database, job_title):
    """
    Plot the degrees on a map of the United States
    :param database: Database with the information of job degrees
    :param job_title: The job to use
    :return:
    """
    degrees = {}
    colors = {
        'unknown': 'lightgreen',
        'ms/phd': 'gold',
        'phd': 'coral',
        'ms': 'royalblue',
        'undergrad': 'sienna'}
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

    for job in database.jobs.find({'search_title': job_title, 'finished_processing': True}):
        # ToDo: Replace is_machine_learning_title with a prediction model that applys to all jobs
        if job_title != 'machine learning' or is_machine_learning_title(job['jobtitle']):
            degree_class = degree_classification(database, job)

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
            'marker': {'color': colors[degree]}})

    fig = {'data': plot_data, 'layout': layout}
    py.plot(fig, filename='job-degree-requirements')


def plot_city_for_degree_requierments(database, job_title, city_coords):
    """
    Plot the number of degree requirements for cities
    :param database: Database with the information of job degrees
    :param job_title: The Job to usse
    :return:
    """
    degree_counts = {}
    city_degrees = {}
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

    for job in database.jobs.find({'search_title': job_title, 'finished_processing': True}):
        # ToDo: Replace is_machine_learning_title with a prediction model that applys to all jobs
        if job_title != 'machine learning' or is_machine_learning_title(job['jobtitle']):
            closest_city = _find_closest_city(city_coords, (job['latitude'], job['longitude']))
            if closest_city:
                degree_class = degree_classification(database, job)
                if degree_class not in city_degrees:
                    city_degrees[degree_class] = []
                if closest_city not in degree_counts:
                    degree_counts[closest_city] = {
                        'unknown': 0,
                        'undergrad': 0,
                        'ms/phd': 0,
                        'ms': 0,
                        'phd': 0}
                degree_counts[closest_city][degree_classification(database, job)] += 1
                city_degrees[degree_class].append(closest_city)

    for degree, cities in city_degrees.items():
        latitudes = []
        longitudes = []
        sizes = []
        for city in cities:
            latitudes.append(city_coords[city][0])
            longitudes.append(city_coords[city][1])
            sizes.append(degree_counts[city][degree])

        plot_data.append({
            'name': degree,
            'type': 'scattergeo',
            'locationmode': 'USA-states',
            'lat': latitudes,
            'lon': longitudes,
            'text': sizes,
            'marker': {
                'size': sizes,
                'sizemode': 'area'}})

    fig = {'data': plot_data, 'layout': layout}
    py.plot(fig, filename='city-job-degree-requirements')
