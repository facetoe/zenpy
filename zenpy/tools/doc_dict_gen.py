import json
import os
from collections import defaultdict

import requests
from bs4 import BeautifulSoup, SoupStrainer

base_url = "https://developer.zendesk.com"


def get_links():
    skippages = (
        '/rest_api/docs/core/introduction',
        '/rest_api/docs/core/getting_started',
        '/rest_api/docs/core/api_changes',
        '/rest_api/docs/core/restrictions',
        '/rest_api/docs/help_center/introduction',
        '/rest_api/docs/zopim/introduction',
        '/rest_api/docs/zopim/restrictions',
        '/rest_api/docs/zopim/changes_roadmap',
        '/rest_api/docs/web-portal/webportal_introduction',
        '/rest_api/docs/nps-api/introduction',
        '/rest_api/docs/core/side_loading',
        '/rest_api/docs/core/search',
        '/rest_api/docs/core/locales'
    )

    print("Retrieving links")
    response = requests.get('https://developer.zendesk.com/rest_api/docs/core/introduction')
    soup = BeautifulSoup(response.content, "lxml")
    nav_section = soup.find("ul", {"class": "docs-sidenav"})

    api_doc_links = []
    for link in [l['href'] for l in nav_section.findAll('a')]:
        if link not in skippages and not link.startswith('#'):
            api_doc_links.append(link)
    return api_doc_links


def parse_link(link):
    print("Parsing link: " + link)
    response = requests.get(base_url + link)

    table_attr = SoupStrainer("table")
    soup = BeautifulSoup(response.content, 'lxml', parse_only=table_attr)

    table = soup.find('table')
    if not table:
        return {}

    rows = table.findAll('tr')
    header = [data.text.lower() for data in rows[0].findAll('th')]

    object_name = os.path.basename(os.path.normpath(link))
    object_info = defaultdict(dict)
    object_info[object_name] = defaultdict(dict)
    for row in rows[1:]:
        columns = [data.text for data in row.findAll('td')]
        row_data = dict(zip(header, columns))
        name = row_data.pop('name')
        object_info[object_name][name].update(row_data)

    print("Parsing Completed for: " + link)
    return object_info


from multiprocessing.pool import ThreadPool

pool = ThreadPool(processes=20)

results = pool.map_async(parse_link, get_links())
output = dict()
for result in results.get():
    output.update(result)

with open('doc_dict.json', 'w+') as f:
    json.dump(output, f)
