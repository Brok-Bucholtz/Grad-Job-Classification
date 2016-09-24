# Grad-Job-Classification
View the market for University Degrees
## Install
```
pip3 install -r requirements.txt
```
Edit ```config.ini``` with your mongodb and indeed information:
```
[INDEED]
PublisherNumber = <Indeed_Publisher_Numer_Here>

[DATABASE]
Name = grad_job_classification
Host = localhost
Port = 27017
```
If you do not have a publisher number, you can receive one by heading to the [Indeed Publisher Portal](http://www.indeed.com/publisher).
## Usage
```
python3 grad_job_classification.py <Task>
```
### Examples
Scrape job data for "machine learning"
```
python3 grad_job_classification.py scrape "machine learning"
```
Visualize job data for "machine learning"
```
python3 grad_job_classification.py analyse "machine learning"
```
