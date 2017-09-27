#!/usr/bin/python

def main():
    project = 'TRANS'
    jira_connect = JiraConnector(url='https://jira.atlassian.com',
                                 limit=10)

    filter_str = 'project = "%s" and resolution = Done order by key desc' % project
    issues = jira_connect.list_all(filter_str)
    for issue in issues:
        print "%s - %s | created %s" % (issue.key, issue.fields.summary, issue.fields.created)
        
if __name__ == '__main__':
    #Construction for relative import
    if __package__ is None:
        import sys
        from os import path
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        from jira_connector import JiraConnector
    else:
        from ..jira_connector import JiraConnector
    main()