from math import floor, ceil, sqrt

from bson import SON
import matplotlib.pyplot as plt

from feature_extraction import job_degree_strings


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
            if 'degree_classification' not in job:
                degree_strings = job_degree_strings(job['html_posting'])
                is_grad = degree_strings['ms'] or degree_strings['phd']
                is_undergrad = degree_strings['undergrad'] and not is_grad

                if is_undergrad:
                    degree_classification = 'undergrad'
                elif is_grad:
                    if degree_strings['ms'] and degree_strings['phd']:
                        degree_classification = 'ms/phd'
                    elif degree_strings['ms']:
                        degree_classification = 'ms'
                    else:
                        degree_classification = 'phd'
                else:
                    degree_classification = 'unknown'

                database.jobs.update_one(
                    {'_id': job['_id']},
                    {'$set': {'degree_classification': degree_classification}})
            else:
                degree_classification = job['degree_classification']

            location_degree_counts[degree_classification] += 1

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
