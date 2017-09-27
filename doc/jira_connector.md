# jira_connector  
JiraConnector class extending [Jira Python](https://github.com/pycontribs/jira) module.

This class provides methods to collect, group and analyse stats from Jira projects.

## Usage

```python
from jira_connector import JiraConnector

project = 'TRANS'
jira_connect = JiraConnector(url='https://jira.atlassian.com', limit=10)

filter_str = 'project = "%s" and resolution = Done order by key desc' % project
issues = jira_connect.list_all(filter_str)

for issue in issues:
    print "%s - %s | created %s" % (issue.key, issue.fields.summary, issue.fields.created)
```  

 __Author__: Alexander Grechin   
 __Version__: 0.2  
 __License__: GNU GPL V2  


## Classes


### class `JiraConnector()`
JiraConnector class  
Attributes:  
url (str): Jira URL like https://jira.atlassian.com  
limit (int, optional): Global limit of captured issues, 100 by default  
count (int, optional): Number of issues captured in the each iteration, 100 by deafult  

### Methods:


#### def `__init__()`
Initialization  

#### def `connect()`
Implicitly connect to Jira  

#### def `get_attachment_filenames(ex_issue)`
Function returns list of attachment filenames  
  
Args:  
issue (obj): Jira extended issue  
  
Returns:  
list: list of string items  

#### def `get_average_date(date_list)`
Function returns average time period between dates in date_list  
  
Args:  
date_list (list): list of dates in string format  
  
Returns:  
string: timedelta  

#### def `get_bug_crit_list(project, version_string)`
Function returns list of major, critical and blocker bugs in project filtered by version  
  
Args:  
project (string): Jira project name  
version_string (string): version specifier  
  
Returns:  
list: list of Jira issues  

#### def `get_bug_list(project, version_string)`
Function returns list of bugs in project filtered by version  
  
Args:  
project (string): Jira project name  
version_string (string): version specifier  
  
Returns:  
list: list of Jira issues  

#### def `get_bug_prod_list(project, version_string, date)`
Function returns list of production bugs in project filtered by version  
  
Args:  
project (string): Jira project name  
version_string (string): version specifier  
date (string): version release date  
  
Returns:  
list: list of Jira issues  

#### def `get_bugfix_list(project, version_string)`
Function returns list of bugsxes in project filtered by version  
  
Args:  
project (string): Jira project name  
version_string (string): version specifier  
  
Returns:  
list: list of Jira issues  

#### def `get_expand_issue(issue)`
Function returns expanded information for an issue  
  
Args:  
issue (obj): The jira issue object  
  
Returns:  
obj: Expanded information  

#### def `get_first_release_version(versions, major_version)`
Function returns the first release version in sorted list by major version  
  
Args:  
versions (list): list of Jits project versions  
major_versions (string): major version specifier  
  
Returns:  
project_version: Jira project version  

#### def `get_issue_by_key(key)`
Function returns issue for a key  
  
Args:  
key (str): An issue key  
  
Returns:  
obj: Jira issue object  

#### def `get_issues_by_version(issues, version_string)`
Function returns list of issues filtered by version  
  
Args:  
issues (list): list of Jira issues  
version_string (string): version specifier  
  
Returns:  
list: list of Jira issues  

#### def `get_items_from_attachment(ex_issue, regex)`
Function returns list of items from attachment filenames of issue  
  
Args:  
issue (obj): Jira extended issue  
regex (str): Custom regex  
  
Returns:  
list: list of string items  

#### def `get_items_from_custom_field(ex_issue, regex, custom_field=customfield_13405)`
Function returns list of items from custom field of issue  
  
Args:  
issue (obj): Jira extended issue  
regex (str): Custom regex  
custom_field (str): Custom field name ("attachment" by default)  
  
Returns:  
list: list of string items  

#### def `get_items_from_description(issue, regex)`
Function returns list of items from issue description by regexp  
  
Args:  
issue (obj): Jira issue  
regex (str): Description filter  
  
Returns:  
list: list of string items  

#### def `get_last_release_version(versions, major_version)`
Function returns the last release version in sorted list by major version  
  
Args:  
versions (list): list of Jits project versions  
major_versions (string): major version specifier  
  
Returns:  
project_version: Jira project version  

#### def `get_last_resolver(issue, status=Developed)`
Function returns the recent resolver name  
  
Args:  
issue (obj): The jira issue object  
  
Returns:  
str: The name of the recent resolver  

#### def `get_release_date(versions, version_string)`
Function returns release date in filtered list by version  
  
Args:  
versions (list): list of Jira project versions  
version_string (string): version specifier  
  
Returns:  
string: Jira release date  

#### def `get_reopen_bug_list(project, version_string)`
Function returns list of reopened bugs in project filtered by version  
  
Args:  
project (string): Jira project name  
version_string (string): version specifier  
  
Returns:  
list: list of Jira issues  

#### def `get_reopen_count(changelog)`
Function returns count of all transitions to Reopen status  
  
Args:  
changelog (obj): Jira issue changelog  
  
Returns:  
int: Count of transitions  

#### def `get_reopen_list(changelog)`
Function returns list of all transitions to Reopen status  
  
Args:  
changelog (obj): Jira issue changelog  
  
Returns:  
list: list of transitions  

#### def `get_resolution_date(changelog, status=Developed)`
Function returns the date of the last resolution  
  
Args:  
changelog (obj): Jira issue changelog  
status (string): status specifier for filtering  
  
Returns:  
date: The date of the last resolution  

#### def `get_start_date(versions, version_string)`
Function returns start date in filtered list by version  
  
Args:  
versions (list): list of Jira project versions  
version_string (string): version specifier  
  
Returns:  
string: Jira release date  

#### def `get_task_list(project, version_string)`
Function returns list of tasks in project filtered by version  
  
Args:  
project (string): Jira project name  
version_string (string): version specifier  
  
Returns:  
list: list of Jira issues  

#### def `get_total_date(date_list)`
Function returns total time period between dates in date_list  
  
Args:  
date_list (list): list of dates in string format  
  
Returns:  
string: timedelta  

#### def `get_transition_by_name(issue, status)`
Function returns index of transition by status name  
Args:  
issue (obj): Jira issue object  
status (str): Issue status name  
Returns:  
int: Jira transition index  

#### def `group_list(all_items, sort_field_name, group_field_name, reverse=True, sort_func=None)`
The function returns item list grouped by field  
  
Args:  
all_items (list): item list (list of dicts)  
sort_field_name (string): field to sort  
group_field_name (string): field to group  
sort_func (string): comparing function  
  
Returns:  
list: list of Jira issues  

#### def `handle_all_issues(filter_str, method=None)`
Function handle list of issues from the filter  
  
Args:  
filter_str (str): Jira JQL filter  
  
Returns:  
list: list of Jira issues  

#### def `list_all(filter_str)`
Function returns list of issues from the filter  
  
Args:  
filter_str (str): Jira JQL filter  
  
Returns:  
list: list of Jira issues  

#### def `numeric(a, b)`
Function implements proper comparison of versions  
  
Args:  
a (string): version specifier  
a (string): version specifier  
  
Returns:  
int: +1 or -1 if a greater or less then b  

#### def `parse_date(date_string)`
Function returns date object  
  
Args:  
date_string (string): date specifier  
  
Returns:  
datetime: date  

#### def `print_all(filter_str)`
Function prints list of issues from the filter  
  
Args:  
filter_str (str): Jira JQL filter  

#### def `transit(issue, transition_name)`
Execute jira transition by the transition name  
Args:  
issue (obj): Jira issue object  
transition_name (str): Jira transition name  
Returns:  
list: (issuetype, key, status, assegnee)  

#### def `transit_all(filter_str, transition_name, dest_status)`
Function transit all issues from the filter  
  
Args:  
filter_str (str): Jira JQL filter  
transition_name (str): Name of transition in Jira workflow  
dest_status (str): Destination status in Jira workflow  