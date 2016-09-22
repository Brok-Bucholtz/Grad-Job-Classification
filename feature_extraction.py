import re

from bs4 import BeautifulSoup


def _job_degree_strings(html):
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
    soup = BeautifulSoup(html, 'html.parser')

    # Remove css and js from search
    for script in soup(["script", "style"]):
        script.extract()

    # Get strings related to degree requierments
    for element in soup(text=re.compile(r'\b[p]\.?[h]\.?[d]\.?\b', flags=re.IGNORECASE)):
        degree_strings['phd'].append(element)
    for element in soup(text=re.compile(r'\b[m]\.?[s]\.?\b', flags=re.IGNORECASE)):
        degree_strings['ms'].append(element)
    for element in soup(text=re.compile(r'\b(degree|bachelors|[b]\.?[s])\b', flags=re.IGNORECASE)): # Bachelors
        degree_strings['undergrad'].append(element)

    return degree_strings


def degree_classification(database, job):
    """
    Get the degree classification for a job from cache, otherwise cache it
    :param database: Database to update job
    :param job: Job to get degree classifivation for
    :return: Degree classification
    """
    if 'degree_classification' not in job:
        degree_strings = _job_degree_strings(job['html_posting'])
        is_grad = degree_strings['ms'] or degree_strings['phd']
        is_undergrad = degree_strings['undergrad'] and not is_grad

        if is_undergrad:
            degree_class = 'undergrad'
        elif is_grad:
            if degree_strings['ms'] and degree_strings['phd']:
                degree_class = 'ms/phd'
            elif degree_strings['ms']:
                degree_class = 'ms'
            else:
                degree_class = 'phd'
        else:
            degree_class = 'unknown'

        database.jobs.update_one(
            {'_id': job['_id']},
            {'$set': {'degree_classification': degree_class}})
    else:
        degree_class = job['degree_classification']

    return degree_class


def is_machine_learning_title(title):
    """
    A quick and easy solution to filter out jobs with titles that don't have anything to do with machine learning.
    This will need to be replace with a prediction model in order to apply to all job types
    :param title: Title of the job
    :return: True if the title is for machine learning job, False otherwise
    """
    return bool(re.search(r'(data|machine\Wlearn|computer scientist)', title, flags=re.IGNORECASE))
