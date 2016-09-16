import argparse
import configparser
import re

from indeed import IndeedClient


# Simplified checking for discovering if a job requires a masters or phd.
# This will be improved in the future
def _is_grad_job(job):
    return re.match(r'[p]\.?[h]\.?[d]\.?', job['snippet'], flags=re.IGNORECASE) or\
        re.match(r'[m]\.?[s]\.?', job['snippet'], flags=re.IGNORECASE)


def run():
    config = configparser.ConfigParser()
    config.read('config.ini')
    parser = argparse.ArgumentParser()
    client = IndeedClient(publisher=config['DEFAULT']['IndeedPublisherNumber'])

    parser.add_argument('JobTitle', help='Search for specific job title', type=str)
    parser.add_argument('Locations', help='Location(s) to search', nargs='+', type=str)
    args = parser.parse_args()

    for location in args.Locations:
        indeed_params = {
            'q': args.JobTitle,
            'l': location,
            'userip': '1.2.3.4',
            'useragent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2)'
        }
        jobs = client.search(**indeed_params)['results']
        grad_jobs = [job for job in jobs if _is_grad_job(job)]

        print('{} found {} matches out of {}'.format(location, len(grad_jobs), len(jobs)))


if __name__ == '__main__':
    run()
