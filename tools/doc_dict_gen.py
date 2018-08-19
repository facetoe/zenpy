import json

import os
import requests
from bs4 import BeautifulSoup, SoupStrainer
from collections import defaultdict

base_url = "https://developer.zendesk.com"


def get_links():
    print("Retrieving links")

    def extract_links(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "lxml")
        nav_section = soup.find("ul", {"class": "docs-sidenav"})

        api_doc_links = []
        for link in [l['href'] for l in nav_section.findAll('a')]:
            if not link.startswith('#'):
                api_doc_links.append(link)
        return api_doc_links

    urls = (
        'https://developer.zendesk.com/rest_api/docs/core/introduction',
        'https://developer.zendesk.com/rest_api/docs/help_center/introduction',
        'https://developer.zendesk.com/rest_api/docs/chat/introduction',
    )

    links = []
    for url in urls:
        links.extend(extract_links(url))
    return links


def parse_link(link):
    namespace = link.split('/')[-2]

    print("Parsing {} link: {}".format(namespace, link))
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
        name = row_data.pop('name', None)
        if name:
            object_info[object_name][name].update(row_data)

    print("Parsing Completed for: " + link)
    return namespace, object_info


from multiprocessing.pool import ThreadPool

with ThreadPool(processes=50) as pool:
    results = pool.map(parse_link, get_links())

output = defaultdict(dict)
for result in results:
    if result:
        namespace, data = result
        output[namespace].update(data)

with open('doc_dict.json', 'w+') as f:
    json.dump(output, f, indent=2)
