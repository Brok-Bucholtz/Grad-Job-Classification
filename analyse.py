from math import floor, ceil, sqrt

from bson import SON
import matplotlib.pyplot as plt
import plotly.plotly as py

from feature_extraction import degree_classification, is_machine_learning_title


def plot_degree_count_piechart(database, job_title):
    """
    Plot pie charts showing the number of degrees per top locations
    :param database: Database with the job data
    :param job_title: Job title to analyse
    :return:
    """
    top_count = 9
    fig = plt.figure()
    most_jobs_pipeline = [
        {'$unwind': '$search_location'},
        {'$group': {'_id': '$search_location', 'count': {'$sum': 1}}},
        {'$sort': SON([('count', -1), ('_id', -1)])}]
    locations_with_most_jobs = [row['_id'] for row in database.jobs.aggregate(most_jobs_pipeline)][:top_count]

    for location_i, location in enumerate(locations_with_most_jobs):
        location_degree_counts = {
            'unknown': 0,
            'undergrad': 0,
            'ms/phd': 0,
            'ms': 0,
            'phd': 0}
        for job in database.jobs.find({'search_title': job_title, 'search_location': location}):
            # ToDo: Replace is_machine_learning_title with a prediction model that applys to all jobs
            if job_title != 'machine learning' or is_machine_learning_title(job['jobtitle']):
                location_degree_counts[degree_classification(database, job)] += 1

        # Create pie chart
        total = sum([count for degree, count in location_degree_counts.items()])
        labels = []
        sizes = []
        colors = ['lightgreen', 'gold', 'coral', 'royalblue', 'sienna']

        for degree, count in location_degree_counts.items():
            labels.append(degree)
            sizes.append(count/total)

        location_plt = fig.add_subplot(floor(sqrt(top_count)), ceil(sqrt(top_count)), location_i+1)
        location_plt.set_title('{} - {}'.format(location, total))
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

    for job in database.jobs.find({'search_title': job_title}):
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
