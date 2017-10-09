#!/usr/bin/python

import logging

def smart_truncate(text, length=40, suffix='...'):
    if len(text) <= length:
        return text
    else:
	return text[:length-len(suffix)].rsplit(' ', 1)[0] + suffix

def main():
    title_width = 40
    fmt = '{0:<8} | {1:%d.%d} | {2:<10}' % (title_width, title_width)
 
    project = 'FE'
    jira_connect = JiraConnector(config='config/config.yml')
    bugs = jira_connect.get_bug_list(project, '1.4.2')
    for bug in bugs:
        if bug.fields.resolutiondate is not None:
            resolution_date = jira_connect.parse_date(bug.fields.resolutiondate)
            print fmt.format(
                bug.key, 
                smart_truncate(bug.fields.summary, title_width), 
                resolution_date.strftime('%Y-%m-%dT%H:%M:%S')
                )
        else:
            print fmt.format(
                bug.key, 
                smart_truncate(bug.fields.summary, title_width), 
                'not fixed'
            )
        
if __name__ == '__main__':
    #Construction for relative import
    if __package__ is None:
        import sys
        from os import path
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        from jira_connector import JiraConnector
    else:
        from jira_connector import JiraConnector
    main()
