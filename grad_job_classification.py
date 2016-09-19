import argparse
import configparser
from dateutil import parser

import pymongo
import requests

from indeed import IndeedClient
from pymongo import MongoClient

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


def scrape_indeed(database, indeed_client, job_title, locations):
    """
    Scrape job data from indeed and save it to the database
    :param database: Database to save the indeed data
    :param indeed_client: Indeed API client
    :param job_title: Job title to search for
    :param locations: Job locations to search for
    :return: 
    """
    max_indeed_limit = 25
    indeed_params = {
        'q': job_title,
        'limit': max_indeed_limit,
        'latlong': 1,
        'sort': 'date',
        'userip': '1.2.3.4',
        'useragent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2)'
    }

    for location in locations:
        result_start = 0
        newest_job = database.jobs.find_one({'search_title': job_title, 'search_location': location},
                                            sort=[('date', pymongo.DESCENDING)])
        indeed_response = indeed_client.search(**indeed_params, l=location, start=result_start)
        jobs = indeed_response['results']
        total_jobs = indeed_response['totalResults']

        while result_start < total_jobs and\
                (not newest_job or newest_job['date'] < parser.parse(jobs[0]['date']).timestamp()):
            new_jobs = []
            for job in jobs:
                found_job = database.jobs.find_one({'jobkey': job['jobkey']})
                if found_job:
                    _update_array_fields(
                        database.jobs,
                        found_job,
                        {'search_location': location, 'search_title': job_title})
                else:
                    job['search_location'] = [location]
                    job['search_title'] = [job_title]
                    job['html_posting'] = requests.get(job['url']).content
                    job['date'] = parser.parse(job['date']).timestamp()
                    new_jobs.append(job)
            if new_jobs:
                database.jobs.insert_many(new_jobs)

            result_start += indeed_params['limit']
            jobs = indeed_client.search(**indeed_params, l=location, start=result_start)['results']


def run():
    config = configparser.ConfigParser()
    config.read('config.ini')
    arg_parser = argparse.ArgumentParser()
    indeed_client = IndeedClient(publisher=config['INDEED']['PublisherNumber'])
    database = MongoClient(config['DATABASE']['Host'], int(config['DATABASE']['Port']))[config['DATABASE']['Name']]

    arg_parser.add_argument('JobTitle', help='Search for specific job title', type=str)
    arg_parser.add_argument('Locations', help='Location(s) to search', nargs='+', type=str)
    args = arg_parser.parse_args()

    scrape_indeed(database, indeed_client, args.JobTitle, args.Locations)

    # Count the degree types found
    city_degree_counts = {}
    for job in database.jobs.find({'search_title': args.JobTitle}):
        for city in job['search_location']:
            if city not in city_degree_counts:
                city_degree_counts[city] = {
                    'undergrad': 0,
                    'ms': 0,
                    'phd': 0}
            for degree, strings in job_degree_strings(job['html_posting']).items():
                if strings:
                    city_degree_counts[city][degree] += 1

    for city, degree_count in city_degree_counts.items():
        print('{} found {} undergrads, {} ms, and {} phd matches'.format(
           city,
           degree_count['undergrad'],
           degree_count['ms'],
           degree_count['phd']))


if __name__ == '__main__':
    run()
