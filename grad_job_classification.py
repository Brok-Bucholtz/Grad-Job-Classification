import argparse
import configparser
import logging

from indeed import IndeedClient
from pymongo import MongoClient

from analyse import plot_degree_count_city_piechart, plot_degree_map, plot_jobs_not_in_city_for_degree_requierments
from feature_extraction import is_machine_learning_title
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
        jobs = []
        major_city_coords = {
            'seattle, washington': (47.6062, -122.3321),
            'The Bay Area': (37.8272, -122.2913),
            'Los Angeles, California': (34.0522, -118.2437),
            'Salt Lake City, Utah': (40.7608, -111.8910),
            'Denver, Colorado': (39.7392, -104.9903),
            'Dallas, Texas': (32.7767, -96.7970),
            'Austin, Texas': (30.2672, -97.7431),
            'Houston, Texas': (29.7604, -95.3698),
            'Minneapolis, Minnesota': (44.9778, -93.2650),
            'Chicago, Illinois': (41.8781, -87.6298),
            'Atlanta, Georgia': (33.7490, -84.3880),
            'Detroit, Michigan': (42.3314, -83.0458),
            'Durham, North Carolina': (35.9940, -78.8986),
            'Miami, Florida': (25.7617, -80.1918),
            'Washington, District of Columbia': (38.9072, -77.0369),
            'Philadelphia, Pennsylvania': (39.9526, -75.1652),
            'Boston, Massachusetts': (42.3601, -71.0589),
            'New York, New York': (40.730610, -73.935242),
            'San Diego, California': (32.715736, -117.161087),
            'Sacramento, California': (38.575764, -121.478851)}

        for job in database.jobs.find(
                {'search_title': args.JobTitle, 'finished_processing': True},
                projection={'jobtitle': True, 'latitude': True, 'longitude': True, 'degree_classification': True}):
            # ToDo: Replace is_machine_learning_title with a prediction model that applys to all jobs
            if args.JobTitle != 'machine learning' or is_machine_learning_title(job['jobtitle']):
                jobs.append(job)

        logger.info('Analysing job data...')
        plot_degree_count_city_piechart(jobs, major_city_coords, True)
        plot_degree_map(jobs)
        plot_jobs_not_in_city_for_degree_requierments(jobs, major_city_coords)
    elif args.TaskType == 'scrape':
        locations = args.locations if args.locations else scrape_cities()

        logger.info('Scraping indeed...')
        indeed_client = IndeedClient(publisher=config['INDEED']['PublisherNumber'])
        scrape_indeed(database, indeed_client, logger, args.JobTitle, locations)


if __name__ == '__main__':
    run()
