import argparse
import configparser
import re
from dateutil import parser

import pymongo
import requests

from bs4 import BeautifulSoup
from indeed import IndeedClient
from pymongo import MongoClient


def job_degree_strings(job):
    """
    Get strings from the job page that are related to degree requirements
    :param job: Indeed job
    :return: Dictionary list of all found strings related to degree.
    """

    degree_strings = {
        'undergrad': [],
        'ms': [],
        'phd': []
    }
    page = requests.get(job['url'])
    soup = BeautifulSoup(page.content, 'html.parser')

    # Remove css and js from search
    for script in soup(["script", "style"]):
        script.extract()

    # Get strings related to degree requierments
    for element in soup(text=re.compile(r'\b[p]\.?[h]\.?[d]\.?\b', flags=re.IGNORECASE)):
        degree_strings['phd'].append(element)
    for element in soup(text=re.compile(r'\b[m]\.?[s]\.?\b', flags=re.IGNORECASE)):
        degree_strings['ms'].append(element)
    for element in soup(text=re.compile(r'\bdegree\b', flags=re.IGNORECASE)):
        degree_strings['undergrad'].append(element)

    return degree_strings


def run():
    max_indeed_limit = 25
    config = configparser.ConfigParser()
    config.read('config.ini')
    arg_parser = argparse.ArgumentParser()
    indeed_client = IndeedClient(publisher=config['INDEED']['PublisherNumber'])
    database = MongoClient(config['DATABASE']['Host'], int(config['DATABASE']['Port']))[config['DATABASE']['Name']]

    arg_parser.add_argument('JobTitle', help='Search for specific job title', type=str)
    arg_parser.add_argument('Locations', help='Location(s) to search', nargs='+', type=str)
    args = arg_parser.parse_args()

    indeed_params = {
        'q': args.JobTitle,
        'limit': max_indeed_limit,
        'latlong': 1,
        'sort': 'date',
        'userip': '1.2.3.4',
        'useragent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2)'
    }

    for location in args.Locations:
        result_start = 0
        newest_job = database.jobs.find_one({'search_location': location}, sort=[('date', pymongo.DESCENDING)])
        indeed_response = indeed_client.search(**indeed_params, l=location, start=result_start)
        jobs = indeed_response['results']
        total_jobs = indeed_response['totalResults']

        while result_start < total_jobs and\
                (not newest_job or newest_job['date'] < parser.parse(jobs[0]['date']).timestamp()):
            new_jobs = [job for job in jobs if not database.jobs.find({'jobkey': job['jobkey']}).count()]
            if new_jobs:
                for job in new_jobs:
                    job['search_location'] = location
                    job['degree_strings'] = job_degree_strings(job)
                    job['date'] = parser.parse(job['date']).timestamp()
                database.jobs.insert_many(new_jobs)

            result_start += indeed_params['limit']
            jobs = indeed_client.search(**indeed_params, l=location, start=result_start)['results']

    # Count the degree types found
    city_degree_counts = {}
    for job in database.jobs.find():
        city = job['search_location']
        if city not in city_degree_counts:
            city_degree_counts[city] = {
                'undergrad': 0,
                'ms': 0,
                'phd': 0}
        for degree, strings in job['degree_strings'].items():
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
