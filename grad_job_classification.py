import argparse
import configparser
import csv
from os import path, makedirs

import ipgetter
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
        'userip': ipgetter.myip(),
        'useragent': 'Python'
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


def analyse(database, job_title):
    """
    Analyse job data from database and print results
    :param database: Database with the job data
    :param job_title: Job title to analyse
    :return:
    """
    city_degree_counts = {}
    for job in database.jobs.find({'search_title': job_title}):
        for city in job['search_location']:
            if city not in city_degree_counts:
                city_degree_counts[city] = {
                    'unknown': 0,
                    'undergrad': 0,
                    'ms/phd': 0,
                    'ms': 0,
                    'phd': 0}
            degree_strings = job_degree_strings(job['html_posting'])
            is_grad = degree_strings['ms'] or degree_strings['phd']
            is_undergrad = degree_strings['undergrad'] and not is_grad

            if is_undergrad:
                city_degree_counts[city]['undergrad'] += 1
            elif is_grad:
                if degree_strings['ms'] and degree_strings['phd']:
                    city_degree_counts[city]['ms/phd'] += 1
                elif degree_strings['ms']:
                    city_degree_counts[city]['ms'] += 1
                else:
                    city_degree_counts[city]['phd'] += 1
            else:
                city_degree_counts[city]['unknown'] += 1

    longest_city_length = len(max(city_degree_counts.keys(), key=len))
    for city, degree_count in city_degree_counts.items():
        output_string =\
            '{:<' +\
            str(longest_city_length) +\
            '} found {:>3} undergrads, {:>3} ms/phd, {:>3} ms, {:>3} phd, and {:>3} unknown matches'
        print(output_string.format(
                city,
                degree_count['undergrad'],
                degree_count['ms/phd'],
                degree_count['ms'],
                degree_count['phd'],
                degree_count['unknown']))


def run():
    config = configparser.ConfigParser()
    config.read('config.ini')
    arg_parser = argparse.ArgumentParser()
    database = MongoClient(config['DATABASE']['Host'], int(config['DATABASE']['Port']))[config['DATABASE']['Name']]

    arg_parser.add_argument('TaskType', help='Run the specified task type', choices=['analyse', 'scrape'], type=str)
    arg_parser.add_argument('JobTitle', help='Search for specific job title', type=str)
    args = arg_parser.parse_args()

    if args.TaskType == 'analyse':
        analyse(database, args.JobTitle)
    elif args.TaskType == 'scrape':
        indeed_client = IndeedClient(publisher=config['INDEED']['PublisherNumber'])
        cities = _scrape_cities()
        scrape_indeed(database, indeed_client, args.JobTitle, cities)


if __name__ == '__main__':
    run()
