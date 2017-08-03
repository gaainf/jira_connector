#!/usr/bin/python
# -*- coding: utf-8 -*-

from jira import JIRA
from jira import JIRAError
import re
import datetime
import dateutil.parser
from distutils.version import LooseVersion, StrictVersion
import operator


# Enable debug
# import httplib
# httplib.HTTPConnection.debuglevel=1


class JiraConnector:
    """Jira connector class"""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        if 'url' not in self.__dict__ or self.url is None:
            self.url = 'https://jira.rambler-co.ru'
        if 'limit' not in self.__dict__ or self.limit is None:
            self.limit = 100
        if 'count' not in self.__dict__ or self.count is None:
            self.count = 100
        if self.count > self.limit:
            self.count = self.limit
        self.options = {'server': self.url}
        self.basic_auth = (self.username, self.password)

        if 'init_connect' not in self.__dict__ or self.init_connect is None or self.init_connect == True:
            self.connect()

    def connect(self):
        try:
            self.jira = JIRA(options=self.options, basic_auth=self.basic_auth)
        except JIRAError as e:
            m = re.search('<title>(.+)</title>', e.text)
            print e.status_code, m.group(1)
            exit()

    def get_items_from_description(self, issue, regex=r'(begun-.*\.rpm|[a-z0-9]{40})'):
        """The function returns list of items from issue description by regexp

        Args:
          issue (obj): Jira issue

        Returns:
          list: list of string items
        """

        packets = []
        if issue.fields.description is not None:
            for m in re.finditer(regex, issue.fields.description):
                packets.append(m.group(1))
        return packets

    def get_items_from_custom_field(self, ex_issue, regex=r'(begun-.*\.rpm)', custom_field='customfield_13405'):
        """The function returns list of items from custom field of issue

        Args:
          issue (obj): Jira extended issue
          regex (str): Custom regex
          custom_field (str): Custom field name

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
        """The function returns list of attachment filenames

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

    def get_items_from_attachment(self, ex_issue, regex=r'(begun-.*\.rpm)'):
        """The function returns list of items from attachment filenames of issue

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
        """The function returns issue for a key

        Args:
          key (str): An issue key

        Returns:
          obj: Jira issue object
        """

        return self.jira.issue(key)

    def get_expand_issue(self, issue):
        """The function returns expanded information for an issue

        Args:
          issue (obj): The jira issue object

        Returns:
          obj: Expanded information
        """

        return self.jira.issue(issue.key, expand='changelog')

    def get_last_resolver(self, issue, status='Developed'):
        """The function returns the recent resolver name

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
        """The function handle list of issues from the filter

        Args:
          filter_str (str): Jira JQL filter

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

    def list_all(self, filter_str):
        """The function returns list of issues from the filter

        Args:
          filter_str (str): Jira JQL filter

        Returns:
           list: list of Jira issues
        """

        return self.handle_all_issues(filter_str)

    def print_all(self, filter_str):
        """The function prints list of issues from the filter

        Args:
          filter_str (str): Jira JQL filter
        """

        def print_issues(issues):
            for issue in issues:
                print template.format(issue.fields.issuetype, issue.key, issue.fields.status)
        template = "{0:15}|{1:15}|{2:15}"
        print template.format("TYPE", "KEY", "STATUS")
        self.handle_all_issues(filter_str, print_issues)

    def transit_all(self, filter_str, transition_name, dest_status):
        """The function transit all issues from the filter

        Args:
          filter_str (str): Jira JQL filter
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
        """The function returns index of transition by status name
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
        """The function returns list of all transitions to Reopen status

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
        """The function returns count of all transitions to Reopen status

        Args:
          changelog (obj): Jira issue changelog

        Returns:
          int: Count of transitions
        """

        return len(self.get_reopen_list(changelog))

    def get_resolution_date(self, changelog, status='Developed'):
        """The function returns the date of the last resolution

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
        """The function returns date object

        Args:
        date_string (string): date specifier

        Returns:
        datetime: date
        """

        if date_string is None:
            return None
        return dateutil.parser.parse(date_string)

    def get_total_date(self, date_list):
        """The function returns total time period between dates in date_list

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
        """The function returns average time period between dates in date_list

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
        """The function returns list of issues filtered by version

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
        """The function implements proper comparison of versions

        Args:
          a (string): version specifier
          a (string): version specifier

        Returns:
          int: +1 or -1 if a greater or less then b
        """

        # if StrictVersion(x) > StrictVersion(y):
        # LooseVersion is used to support 1.1.1.1 instead of canonical 1.1.1
        if LooseVersion(a) > LooseVersion(b):
            return 1
        return -1

    def get_first_release_version(self, versions, major_version):
        """The function returns the first release version in sorted list by major version

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
        """The function returns the last release version in sorted list by major version

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
        """The function returns release date in filtered list by version

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
        """The function returns start date in filtered list by version

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
        """The function returns list of bugs in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier

        Returns:
            list: list of Jira issues
        """

        filter_str = 'project = %s and issuetype = Bug and affectedVersion = "%s" order by key desc' % (
            project, version_string)
        return self.list_all(filter_str)

    def get_bug_crit_list(self, project, version_string):
        """The function returns list of major, critical and blocker bugs in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier

        Returns:
            list: list of Jira issues
        """

        filter_str = 'project = %s and issuetype = Bug and affectedVersion = "%s" and priority > Major order by key desc' % (
            project, version_string)
        return self.list_all(filter_str)

    def get_reopen_bug_list(self, project, version_string):
        """The function returns list of reopened bugs in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier

        Returns:
            list: list of Jira issues
        """

        filter_str = 'project = %s and issuetype = Bug and affectedVersion = "%s" and status was Reopened order by key desc' % (
            project, version_string)
        return self.list_all(filter_str)

    def get_bug_prod_list(self, project, version_string, date):
        """The function returns list of production bugs in project filtered by version

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
        filter_str = 'project = %s and issuetype = Bug and affectedVersion = "%s" and created >= "%s" order by key desc' % (
            project, version_string, date_string)
        return self.list_all(filter_str)

    def get_bugfix_list(self, project, version_string):
        """The function returns list of bugsxes in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier

        Returns:
            list: list of Jira issues
        """

        filter_str = 'project = %s and issuetype = Bug and fixVersion = "%s" order by key desc' % (
            project, version_string)
        return self.list_all(filter_str)

    def get_task_list(self, project, version_string):
        """The function returns list of tasks in project filtered by version

        Args:
            project (string): Jira project name
            version_string (string): version specifier

        Returns:
            list: list of Jira issues
        """

        filter_str = 'project = %s and issuetype != Bug and fixVersion = "%s" order by key desc' % (
            project, version_string)
        return self.list_all(filter_str)
