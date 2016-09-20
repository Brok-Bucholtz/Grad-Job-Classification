import argparse
import configparser
import csv
import logging
from os import path, makedirs
from math import sqrt, ceil, floor
from bson.son import SON

import ipgetter
import requests
import matplotlib.pyplot as plt
from dateutil import parser
from indeed import IndeedClient
from pymongo import MongoClient, DESCENDING

from feature_extraction import job_degree_strings


def _update_array_fields(model, current_values, new_field_values):
    """
    Update all array fields if they don't contain the new values
    :param model: DB Base Model
    :param current_values: Dictionary of current values for model
    :param new_field_values: Dictionary of new values that should be in arrays
    :return:
    """
    update_array_fields = {}
    for field, value in new_field_values.items():
        if value not in current_values[field]:
            update_array_fields[field] = value

    if update_array_fields:
        model.update_one({'_id': current_values['_id']}, {'$push': update_array_fields})


def _scrape_cities():
    """
    Get list of cities in the United States with a population of at least 15,000
    :return: Cities
    """
    cities = []
    cities_file_path = './submodule/world-cities/data/world-cities.csv'
    cache_folder_path = './cache/'
    cities_cache_filename = 'world-cities.csv'

    if not path.exists(cache_folder_path):
        makedirs(cache_folder_path)
    if not path.exists(cache_folder_path + cities_cache_filename):
        # Read raw city data
        with open(cities_file_path) as file:
            reader = csv.reader(file)
            for row in reader:
                if row[1] == 'United States':
                    cities.append(row[0] + ', ' + row[2])

        # Cache formatted data
        with open(cache_folder_path + cities_cache_filename, 'w+') as file:
            writer = csv.writer(file)
            for city in cities:
                writer.writerow([city])
    else:
        # Read from cache
        with open(cache_folder_path + cities_cache_filename) as file:
            reader = csv.reader(file)
            cities = [row[0] for row in reader]

    return cities


def scrape_indeed(database, indeed_client, logger, job_title, locations):
    """
    Scrape job data from indeed and save it to the database
    :param database: Database to save the indeed data
    :param indeed_client: Indeed API client
    :param logger: Logger to log activity
    :param job_title: Job title to search for
    :param locations: Job locations to search for
    :return: 
    """
    max_indeed_limit = 25
    sample_max_city_name_length = 35
    indeed_params = {
        'q': job_title,
        'limit': max_indeed_limit,
        'latlong': 1,
        'sort': 'date',
        'userip': ipgetter.myip(),
        'useragent': 'Python'
    }

    for location in locations:
        # Using a dicts instead of a list will prevent from adding duplicates
        new_jobs = {}
        update_jobs = {}
        result_start = 0
        newest_job = database.jobs.find_one({'search_title': job_title, 'search_location': location},
                                            sort=[('date', DESCENDING)])
        indeed_response = indeed_client.search(**indeed_params, l=location, start=result_start)
        jobs = indeed_response['results']
        total_jobs = indeed_response['totalResults']

        while result_start < total_jobs and\
                (not newest_job or newest_job['date'] < parser.parse(jobs[0]['date']).timestamp()):
            for job in jobs:
                found_job = database.jobs.find_one({'jobkey': job['jobkey']})
                if found_job:
                    update_jobs[found_job['jobkey']] = found_job
                else:
                    job['search_location'] = [location]
                    job['search_title'] = [job_title]
                    job['html_posting'] = requests.get(job['url']).content
                    job['date'] = parser.parse(job['date']).timestamp()
                    new_jobs[job['jobkey']] = job

            result_start += indeed_params['limit']
            jobs = indeed_client.search(**indeed_params, l=location, start=result_start)['results']

        try:
            if new_jobs:
                debug_log_string = 'Scraped location {:<' + str(sample_max_city_name_length) + '} found {:>3} jobs.'
                logger.debug(debug_log_string.format(location, len(new_jobs)))
                database.jobs.insert_many(new_jobs.values())
            for update_job in update_jobs:
                _update_array_fields(
                    database.jobs,
                    update_job,
                    {'search_location': location, 'search_title': job_title})
        except Exception as error:
            logger.error('Updating db for search_location {} scrape data failed: {}'.format(location, error))


def analyse(database, job_title):
    """
    Analyse job data from database and show results
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
            degree_strings = job_degree_strings(job['html_posting'])
            is_grad = degree_strings['ms'] or degree_strings['phd']
            is_undergrad = degree_strings['undergrad'] and not is_grad

            if is_undergrad:
                location_degree_counts['undergrad'] += 1
            elif is_grad:
                if degree_strings['ms'] and degree_strings['phd']:
                    location_degree_counts['ms/phd'] += 1
                elif degree_strings['ms']:
                    location_degree_counts['ms'] += 1
                else:
                    location_degree_counts['phd'] += 1
            else:
                location_degree_counts['unknown'] += 1

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


def run():
    app_name = 'grad_job_classification'
    config = configparser.ConfigParser()
    config.read('config.ini')
    arg_parser = argparse.ArgumentParser()
    database = MongoClient(config['DATABASE']['Host'], int(config['DATABASE']['Port']))[config['DATABASE']['Name']]

    arg_parser.add_argument('TaskType', help='Run the specified task type', choices=['analyse', 'scrape'], type=str)
    arg_parser.add_argument('JobTitle', help='Search for specific job title', type=str)
    arg_parser.add_argument('--locations', help='Specify the locations to use', nargs='+', type=str)
    arg_parser.add_argument('--verbose', help='Verbose Mode', action='store_true')
    args = arg_parser.parse_args()

    # Setup logging
    logger = logging.getLogger(app_name)
    log_format = logging.Formatter(
        '%(asctime)s [%(process)d][%(levelname)-8s-{:>7}]  --  %(message)s'.format(args.TaskType))
    console = logging.StreamHandler()
    console.setFormatter(log_format)
    logger.addHandler(console)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if args.TaskType == 'analyse':
        logger.info('Analysing job data...')
        analyse(database, args.JobTitle)
    elif args.TaskType == 'scrape':
        locations = []
        if args.locations:
            locations = args.locations
        else:
            locations = _scrape_cities()

        logger.info('Scraping indeed...')
        indeed_client = IndeedClient(publisher=config['INDEED']['PublisherNumber'])
        scrape_indeed(database, indeed_client, logger, args.JobTitle, locations)


if __name__ == '__main__':
    run()
