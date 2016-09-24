import argparse
import configparser
import logging

import pandas as pd
from indeed import IndeedClient
from pymongo import MongoClient

from analyse import plot_degree_count_city_bar_chart, plot_degree_map, plot_jobs_not_in_city_for_degree_requierments
from scrape import scrape_indeed, scrape_cities


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
        major_city_coords = {
            'seattle, WA': (47.6062, -122.3321),
            'San Francisco, CA ': (37.773972, -122.431297),
            'San Jose, CA': (37.279518, -121.867905),
            'Oakland, CA': (37.8043700, -122.2708000),
            'Los Angeles, CA': (34.0522, -118.2437),
            'Salt Lake City, UT': (40.7608, -111.8910),
            'Denver, CO': (39.7392, -104.9903),
            'Dallas, TX': (32.7767, -96.7970),
            'Austin, TX': (30.2672, -97.7431),
            'Houston, TX': (29.7604, -95.3698),
            'Minneapolis, MN': (44.9778, -93.2650),
            'Chicago, IL': (41.8781, -87.6298),
            'Atlanta, GA': (33.7490, -84.3880),
            'Detroit, MI': (42.3314, -83.0458),
            'Durham, North CA': (35.9940, -78.8986),
            'Miami, FL': (25.7617, -80.1918),
            'Washington, DC': (38.9072, -77.0369),
            'Philadelphia, PC': (39.9526, -75.1652),
            'Boston, MA': (42.3601, -71.0589),
            'New York, NY': (40.730610, -73.935242),
            'San Diego, CA': (32.715736, -117.161087),
            'Sacramento, CA': (38.575764, -121.478851)}

        jobs = pd.DataFrame(list(database.jobs.find(
                {'search_title': args.JobTitle, 'finished_processing': True},
                projection={'jobtitle': True, 'latitude': True, 'longitude': True, 'degree_classification': True})))

        # ToDo: Use a prediction model that can be applied to all jobs
        if args.JobTitle == 'machine learning':
            jobs = jobs[jobs['jobtitle'].str.contains(r'(data|machine\Wlearn|computer scientist)', case=False)]

        logger.info('Analysing job data...')
        plot_degree_count_city_bar_chart(jobs, major_city_coords, True)
        plot_degree_map(jobs)
        plot_jobs_not_in_city_for_degree_requierments(jobs, major_city_coords)
    elif args.TaskType == 'scrape':
        locations = args.locations if args.locations else scrape_cities()

        logger.info('Scraping indeed...')
        indeed_client = IndeedClient(publisher=config['INDEED']['PublisherNumber'])
        scrape_indeed(database, indeed_client, logger, args.JobTitle, locations)


if __name__ == '__main__':
    run()
