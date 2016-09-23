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


def degree_classification(html_posting):
    """
    Get the degree classification from a job posting
    :param html_posting: Html of job posting
    :return: Degree classification
    """
    degree_strings = _job_degree_strings(html_posting)
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

    return degree_class
