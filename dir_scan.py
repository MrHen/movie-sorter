from pprint import pprint
import re
import requests


def scan_node(url):
    links_regex = r'<a href="([^.][^\"]+)">[^<]+</a>'
    response = requests.get(url)
    pprint(response.status_code)
    content = response.text
    links = re.findall(links_regex, content)
    return links


todo = [
    'https://dl3.3rver.org/cdn2/02/film/',
]
completed = []
files = []

max_visited = 10

while todo and len(completed) < max_visited:
    url = todo.pop()
    if url.endswith('/'):
        print(url)
    else:
        print(f'Skipping {url}')
        files.append(url)
        continue
    links = scan_node(url)
    completed.append(url)
    todo = [
        *todo,
        *[
            f'{url}{link}'
            for link in links
        ]
    ]
