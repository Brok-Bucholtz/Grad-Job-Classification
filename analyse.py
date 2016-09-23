from math import floor, ceil, sqrt, hypot

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


def _equal_domains(size, spacing, max_length=1):
    """
    Create a list of <size> equal domains of with <spacing> amount in between
    :param size: Number of domains
    :param spacing: Spacing between domains
    :param max_length: Max length of all domains combined
    :return: Equal domains list
    """
    domains = []
    length = (max_length - (spacing * (size - 1))) / size
    
    for x_i in range(size):
        first = x_i * length + x_i * spacing
        second = (x_i + 1) * length + x_i * spacing
        domains.append([first, second])
        
    return domains


def plot_degree_count_city_piechart(jobs, city_coords, include_others=False):
    """
    Plot pie charts showing the number of degrees for cities
    :param jobs: Jobs with degree requirement information
    :param city_coords: Dict of city names to their gps coordinates
    :param include_others: Boolean to include jobs that aren't near cities as their own category
    :return:
    """
    city_degree_counts = {}
    plt_data = []
    for job in jobs:
        closest_city = _find_closest_city(city_coords, (job['latitude'], job['longitude']))
        if include_others and not closest_city:
            closest_city = 'other'

        if closest_city not in city_degree_counts:
            city_degree_counts[closest_city] = {
                'unknown': 0,
                'undergrad': 0,
                'ms/phd': 0,
                'ms': 0,
                'phd': 0}
        city_degree_counts[closest_city][job['degree_classification']] += 1

    # Create coordinates for pie charts
    if len(city_degree_counts) <= 1:
        domains = [[0.3, 0.6]]
    else:
        domains = _equal_domains(ceil(sqrt(len(city_degree_counts))), 0.01)

    # Create pie charts
    for city_i, (city, degree_counts) in enumerate(city_degree_counts.items()):
        labels = []
        sizes = []
        total = sum([count for degree, count in degree_counts.items()])
        for degree, degree_count in degree_counts.items():
            labels.append(degree)
            sizes.append(degree_count/total)

        plt_data.append({
            'values': sizes,
            'labels': labels,
            'name': '{} - {}'.format(city, total),
            'hoverinfo': 'label+percent+name',
            'domain': {'x': domains[city_i % len(domains)], 'y': domains[floor(city_i/len(domains))]},
            'textinfo': 'none',
            'marker': {'colors': [DEGREE_COLORS[degree] for degree in labels]},
            'type': 'pie'})
    py.plot({'data': plt_data})


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
