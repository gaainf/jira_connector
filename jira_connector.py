#!/usr/bin/python
# -*- coding: utf-8 -*-

"""JiraConnector class extending [Jira Python](https://github.com/pycontribs/jira) module.

This class provides methods to collect, group and analyse stats from Jira projects.

## Usage

```python
from jira_connector import JiraConnector

project = 'TRANS'
jira_connect = JiraConnector(url='https://jira.atlassian.com', limit=10)

filter_string = 'project="%s" and resolution=Done order by key desc' % project
issues = jira_connect.list_all(filter_string)

for issue in issues:
    print "%s - %s | created %s" % (issue.key, issue.fields.summary, issue.fields.created)
```

"""

import re
import datetime
from distutils.version import LooseVersion
import operator
import itertools
import dateutil.parser
from jira import JIRA
from jira import JIRAError

__author__ = "Alexander Grechin"
__version__ = "0.3"
__maintainer__ = "Alexander Grechin"
__license__ = "GNU GPL V2"

# Uncomment to debug HTTP
# import httplib
# httplib.HTTPConnection.debuglevel=1

# pylint: disable=R0904
class JiraConnector(object):
    """JiraConnector class
        Attributes:
            url (str): Jira URL like https://jira.atlassian.com
            limit (int, optional): Global limit of captured issues, 100 by default
            count (int, optional): Number of issues captured in the each iteration, 100 by deafult
            config (str): path to config file in YAML format, which add and replace direct values
    """

    url = 'https://jira.atlassian.com'

    def __init__(self, **kwargs):
        """Initialization"""
        if 'config' in kwargs and kwargs['config'] is not None:
            try:
                with open(kwargs['config'], "r") as config_file:
                    try:
                        import yaml
                        config = yaml.load(config_file)
                        self.__dict__.update(config)
                        for key in config:
                            if key in kwargs and kwargs[key] is None:
                                kwargs[key] = config[key]
                    except yaml.YAMLError as e:
                        print(e.problem)
            except ImportError as e:
                print e.message
        #repeate to overwrite config
        self.__dict__.update(kwargs)
        if 'url' not in self.__dict__ or self.url is None:
            self.url = 'https://jira.atlassian.com'
        if 'limit' not in self.__dict__ or self.limit is None:
            self.limit = 100
        if 'count' not in self.__dict__ or self.count is None:
            self.count = 100
        if self.count > self.limit:
            self.count = self.limit
        self.limit = int(self.limit)
        self.count = int(self.count)
        self.options = {'server': self.url}
        if 'username' in self.__dict__ and 'password' in self.__dict__:
            self.basic_auth = (self.username, self.password)

        if 'init_connect' not in self.__dict__ or self.init_connect is None or self.init_connect == True:
            self.connect()

    def connect(self):
        """Implicitly connect to Jira"""
        try:
            if 'basic_auth' in self.__dict__:
                self.jira = JIRA(options=self.options, basic_auth=self.basic_auth)
            else:
                self.jira = JIRA(options=self.options)
            #self.jira = JIRA(options=self.options)
        except JIRAError as e:
            m = re.search('<title>(.+)</title>', e.response)
            print e.status_code, m.group(1)
            print e.status, e.message
            exit()

    def get_items_from_description(self, issue, regex):
        """Function returns list of items from issue description by regexp

        Args:
          issue (obj): Jira issue
          regex (str): Description filter

        Returns:
          list: list of string items
        """

        packets = []
        if issue.fields.description is not None:
            for m in re.finditer(regex, issue.fields.description):
                packets.append(m.group(1))
        return packets

    def get_items_from_custom_field(self, ex_issue, regex, custom_field='customfield_13405'):
        """Function returns list of items from custom field of issue

        Args:
          issue (obj): Jira extended issue
          regex (str): Custom regex
          custom_field (str): Custom field name ("attachment" by default)

        Returns:
          list: list of string items
        """

        packets = []
        attr = getattr(ex_issue.fields, custom_field)
        if attr is not None:
            m = re.match(regex, attr)
            if m is not None:
                packets.append(m.group(1))
        return packets

    def get_attachment_filenames(self, ex_issue):
        """Function returns list of attachment filenames

        Args:
          issue (obj): Jira extended issue

        Returns:
          list: list of string items
        """

        attachments = []
        attr = getattr(ex_issue.fields, 'attachment')
        if attr is not None:
            for attach in attr:
                attachments.append(attach.filename)
        return attachments

    def get_items_from_attachment(self, ex_issue, regex):
        """Function returns list of items from attachment filenames of issue

        Args:
          issue (obj): Jira extended issue
          regex (str): Custom regex

        Returns:
          list: list of string items
        """

        items = []
        attachments = self.get_attachment_filenames(ex_issue)
        for attach in attachments:
            m = re.match(regex, attach)
            if m is not None:
                items.append(m.group(1))
        return items

    def get_issue_by_key(self, key):
        """Function returns issue for a key

        Args:
          key (str): An issue key

        Returns:
          obj: Jira issue object
        """

        return self.jira.issue(key)

    def get_expand_issue(self, issue):
        """Function returns expanded information for an issue

        Args:
          issue (obj): The jira issue object

        Returns:
          obj: Expanded information
        """

        return self.jira.issue(issue.key, expand='changelog')

    def get_last_resolver(self, issue, status='Developed'):
        """Function returns the recent resolver name

        Args:
          issue (obj): The jira issue object

        Returns:
          str: The name of the recent resolver
        """

        resolver = ''
        ex_issue = self.jira.issue(issue.key, expand='changelog')
        changelog = ex_issue.changelog
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'status' and item.toString == status:
                    # print ex_issue.raw
                    # print 'Date:' + history.created + ' From:' +
                    # item.fromString + ' To:' + item.toString + ' By:' +
                    # history.author.name
                    resolver = history.author.name
        return resolver

    def handle_all_issues(self, filter_str, method=None):
        """Function handle list of issues from the filter

        Args:
          filter_string (str): Jira JQL filter

        Returns:
          list: list of Jira issues
        """

        all_issues = []
        start = 0
        template = "{0:15}|{1:15}|{2:15}"
        while start < self.limit:
            issues = self.jira.search_issues(
                filter_str, startAt=start, maxResults=self.count)
            start = start + self.count
            if len(issues) == 0:
                break
            else:
                all_issues.extend(issues)
                if method is not None:
                    method(issues)
        return all_issues

    def list_all(self, filter_string):
        """Function returns list of issues from the filter

        Args:
          filter_string (str): Jira JQL filter

        Returns:
           list: list of Jira issues
        """

        return self.handle_all_issues(filter_string)

    def print_all(self, filter_string):
        """Function prints list of issues from the filter

        Args:
          filter_string (str): Jira JQL filter
        """

        def print_issues(issues):
            for issue in issues:
                print template.format(issue.fields.issuetype, issue.key, issue.fields.status)
        template = "{0:15}|{1:15}|{2:15}"
        print template.format("TYPE", "KEY", "STATUS")
        self.handle_all_issues(filter_str, print_issues)

    def transit_all(self, filter_str, transition_name, dest_status):
        """Function transit all issues from the filter

        Args:
          filter_string (str): Jira JQL filter
          transition_name (str): Name of transition in Jira workflow
          dest_status (str): Destination status in Jira workflow
        """

        def transit_issue(issues):
            for issue in issues:
                print "%s\t\t%s - %s" % (issue.fields.issuetype, issue.key, issue.fields.status)
                transit_list = self.transit(issue, transition_name)
                if transit_list['status'] <> dest_status:
                    print "WARNING: status was not changed, %s expected, %s is actual status" % (dest_status, transit_list['status'])
        self.handle_all_issues(filter_str, transit_issue)

    def get_transition_by_name(self, issue, status):
        """Function returns index of transition by status name
        Args:
          issue (obj): Jira issue object
          status (str): Issue status name
        Returns:
          int: Jira transition index
        """

        index = 0
        transition_list = self.jira.transitions(issue)
        if any(n['name'] == status for n in transition_list):
            index = filter(lambda n: n.get('name') ==
                           status, transition_list)[0]['id']
        return index

    def transit(self, issue, transition_name):
        """Execute jira transition by the transition name
        Args:
          issue (obj): Jira issue object
          transition_name (str): Jira transition name
        Returns:
          list: (issuetype, key, status, assegnee)
        """

        transition_id = self.get_transition_by_name(issue, transition_name)
        if transition_id > 0:
            resolver = self.get_last_resolver(issue)
            issue.update(assignee={'name': resolver})
            # print '\tAvailable transitions: ' + str([(t['id'], t['name']) for
            # t in jira.transitions(issue)]).strip('[]')
            self.jira.transition_issue(issue, transition_id)
            issue = self.jira.issue(issue.key)
        return {'type': issue.fields.issuetype.name,
                'key': issue.key,
                'status': issue.fields.status.name,
                'assignee': issue.fields.assignee.name}

    def get_reopen_list(self, changelog):
        """Function returns list of all transitions to Reopen status

        Args:
          changelog (obj): Jira issue changelog

        Returns:
          list: list of transitions
        """

        all_items = []
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'status' and item.toString == 'Reopened':
                    all_items.append(item)
        return all_items

    def get_reopen_count(self, changelog):
        """Function returns count of all transitions to Reopen status

        Args:
          changelog (obj): Jira issue changelog

        Returns:
          int: Count of transitions
        """

        return len(self.get_reopen_list(changelog))

    def get_resolution_date(self, changelog, status='Developed'):
        """Function returns the date of the last resolution

        Args:
          changelog (obj): Jira issue changelog
          status (string): status specifier for filtering

        Returns:
          date: The date of the last resolution
        """

        date = None
        all_items = []
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'status' and item.toString == status:
                    all_items.append(history.created)
        if len(all_items) > 0:
            date = all_items[-1]
        return date

    def parse_date(self, date_string):
        """Function returns date object

        Args:
        date_string (string): date specifier

        Returns:
        datetime: date
        """

        if date_string is None:
            return None
        return dateutil.parser.parse(date_string)

    def get_total_date(self, date_list):
        """Function returns total time period between dates in date_list

        Args:
          date_list (list): list of dates in string format

        Returns:
          string: timedelta
        """

        diff_list = []
        result = datetime.timedelta(0)
        date_list = sorted(date_list)
        if date_list:
            for i in range(len(date_list) - 1):
                if date_list[i] and date_list[i + 1]:
                    diff = self.parse_date(date_list[i + 1]) - \
                        self.parse_date(date_list[i])
                    diff_list.append(diff)
            if len(diff_list) > 0:
                # result = '"' + str(datetime.timedelta(seconds=(sum(diff_list,
                # datetime.timedelta()).total_seconds()))) + '"'
                result = datetime.timedelta(seconds=(sum(diff_list,
                                                         datetime.timedelta()).total_seconds()))
        return result

    def get_average_date(self, date_list):
        """Function returns average time period between dates in date_list

        Args:
          date_list (list): list of dates in string format

        Returns:
          string: timedelta
        """

        diff_list = []
        result = '0'
        # 2017-01-23T17:00:40.000+0300
        for i in range(len(date_list) - 1):
            if date_list[i] and date_list[i + 1]:
                # datetime_object = datetime.strptime(date_list[i], '%Y-%m-%dT%H:%M:%S.%f%Z')
                diff = self.parse_date(date_list[i]) - \
                    self.parse_date(date_list[i + 1])
                diff_list.append(diff)
        if len(diff_list) > 0:
            result = datetime.timedelta(seconds=(sum(diff_list,
                                                     datetime.timedelta()).total_seconds() / len(diff_list)))
        return result

    def get_issues_by_version(self, issues, version_string):
        """Function returns list of issues filtered by version

        Args:
          issues (list): list of Jira issues
          version_string (string): version specifier

        Returns:
          list: list of Jira issues
        """

        found_issues = None
        found_issues = filter(lambda x: re.search(
            version_string + '(?:$|\s+)', x.fields.summary), issues)
        return found_issues

    def numeric(self, a, b):
        """Function implements proper comparison of versions

        Args:
          a (string): version specifier
          b (string): version specifier

        Returns:
          int: +1 or -1 if a greater or less then b
        """

        # if StrictVersion(x) > StrictVersion(y):
        # LooseVersion is used to support 1.1.1.1 instead of canonical 1.1.1
        if LooseVersion(a) > LooseVersion(b):
            return 1
        return -1

    def get_first_release_version(self, versions, major_version):
        """Function returns the first release version in sorted list by major version

        Args:
          versions (list): list of Jits project versions
          major_versions (string): major version specifier

        Returns:
          project_version: Jira project version
        """

        version_list = filter(lambda x: re.search(
            "^" + major_version + '(?:$|\.)', x.name), versions)
        version_list = sorted(version_list, key=operator.attrgetter(
            'name'), cmp=self.numeric, reverse=False)
        if version_list:
            return getattr(version_list[0], 'name', None)
        return None

    def get_last_release_version(self, versions, major_version):
        """Function returns the last release version in sorted list by major version

        Args:
          versions (list): list of Jits project versions
          major_versions (string): major version specifier

        Returns:
          project_version: Jira project version
        """

        version_list = filter(lambda x: re.search(
            "^" + major_version + '(?:$|\.)', x.name), versions)
        version_list = sorted(version_list, key=operator.attrgetter(
            'name'), cmp=self.numeric, reverse=True)
        if version_list:
            return getattr(version_list[0], 'name', None)
        return None

    def get_release_date(self, versions, version_string):
        """Function returns release date in filtered list by version

        Args:
          versions (list): list of Jira project versions
          version_string (string): version specifier

        Returns:
          string: Jira release date
        """

        version_list = None
        if version_string:
            version_list = filter(lambda x: version_string in x.name, versions)
        if version_list:
            return getattr(version_list[0], 'releaseDate', None)
        return None

    def get_start_date(self, versions, version_string):
        """Function returns start date in filtered list by version

        Args:
          versions (list): list of Jira project versions
          version_string (string): version specifier

        Returns:
          string: Jira release date
        """

        version_list = None
        if version_string:
            version_list = filter(lambda x: version_string in x.name, versions)
        if version_list:
            return getattr(version_list[0], 'startDate', None)
        return None

    def get_bug_list(self, project, version_string):
        """Function returns list of bugs in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier

        Returns:
            list: list of Jira issues
        """

        if 'bug_filter_string' not in self.__dict__:
            filter_string = 'project="{project}" and issuetype = Bug and affectedVersion = "{version_string}" order by key desc'
        else:
            filter_string = self.bug_filter_string
        return self.list_all(filter_string.format(
            project=project,
            version_string=version_string))

    def get_bug_crit_list(self, project, version_string):
        """Function returns list of major, critical and blocker bugs in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier

        Returns:
            list: list of Jira issues
        """

        if 'bug_crit_filter_string' not in self.__dict__:
            filter_string = 'project="{project}" and issuetype=Bug and affectedVersion="{version_string}" and priority>Major order by key desc'
        else:
            filter_string = self.bug_crit_filter_string
        return self.list_all(filter_string.format(
            project=project,
            version_string=version_string))

    def get_reopen_bug_list(self, project, version_string):
        """Function returns list of reopened bugs in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier

        Returns:
            list: list of Jira issues
        """

        if 'bug_reopen_filter_string' not in self.__dict__:
            filter_string = 'project="{project}" and issuetype=Bug and affectedVersion="{version_string}" and status was Reopened order by key desc'
        else:
            filter_string = self.bug_reopen_filter_string
        return self.list_all(filter_string.format(
            project=project,
            version_string=version_string))

    def get_bug_prod_list(self, project, version_string, date):
        """Function returns list of production bugs in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier
            date (string): version release date

        Returns:
            list: list of Jira issues
        """

        if project is None or version_string is None or date is None:
            return []
        datetime_object = self.parse_date(date)
        date_string = datetime_object.strftime("%Y-%m-%d %H:%M")
        if 'bug_prod_filter_string' not in self.__dict__:
            filter_string = 'project="{project}" and issuetype=Bug and affectedVersion="{version_string}" and created>="{date}" order by key desc'
        else:
            filter_string = self.bug_prod_filter_string
        return self.list_all(filter_string.format(
            project=project,
            version_string=version_string,
            date=date_string))

    def get_bugfix_list(self, project, version_string):
        """Function returns list of bugsxes in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier

        Returns:
            list: list of Jira issues
        """

        if 'bugfix_filter_string' not in self.__dict__:
            filter_string = 'project="{project}" and issuetype=Bug and fixVersion="{version_string}" order by key desc'
        else:
            filter_string = self.bugfix_filter_string
        return self.list_all(filter_string.format(
            project=project,
            version_string=version_string))

    def get_task_list(self, project, version_string):
        """Function returns list of tasks in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier

        Returns:
            list: list of Jira issues
        """

        if 'task_filter_string' not in self.__dict__:
            filter_string = 'project="{project}" and issuetype!=Bug and fixVersion="{version_string}" order by key desc'
        else:
            filter_string = self.task_filter_string
        return self.list_all(filter_string.format(
            project=project,
            version_string=version_string))

    def group_list(self, all_items, sort_field_name, group_field_name, reverse=True, sort_func=None):
        """The function returns item list grouped by field

        Args:
            all_items (list): item list (list of dicts)
            sort_field_name (string): field to sort
            group_field_name (string): field to group
            sort_func (string): comparing function

        Returns:
            list: list of Jira issues
        """
        temp_list = []
        if sort_func is None:
            sort_func = self.numeric
        for key, items in itertools.groupby(sorted(all_items,
                                                key=operator.itemgetter(
                                                    sort_field_name),
                                                cmp=sort_func,
                                                reverse=reverse),
                                            operator.itemgetter(group_field_name)):
            temp_list.append(list(items))
        return temp_list
