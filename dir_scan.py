from pprint import pprint
import re
import requests


ALLOWED_EXT = {'mp4', 'mkv'}
REJECTED_EXT = {'srt'}

SKIP_REGEX = r'trailer'


def scan_node(url):
    links_regex = r'<a href="([^.][^\"]+)">[^<]+</a>'
    response = requests.get(url)
    if response.status_code != 200:
        pprint(response.status_code)
    content = response.text
    links = re.findall(links_regex, content)
    return links


todo = [
    'https://dl3.3rver.org/cdn2/02/film/',
]
completed = []
matches = []
mismatches = []
unknown = []

matched_dirs = []

max_visited = 100

while todo and len(completed) < max_visited:
    url = todo.pop()
    if url.endswith('/'):
        print(f'DIR \t{url}')
    elif url.endswith(tuple(ALLOWED_EXT)):
        if re.match(SKIP_REGEX, url, re.IGNORECASE):
            continue
        print(f'MATCH \t{url}')
        matches.append(url)
        matched_dirs.append(url.split('/')[-2])
        continue
    elif url.endswith(tuple(REJECTED_EXT)):
        print(f'MISMATCH \t{url}')
        mismatches.append(url)
        continue
    else:
        print(f'UNKNOWN \t{url}')
        unknown.append(url)
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


'''
cells = document.querySelectorAll('tr td:nth-child(2)');
titles = [];
cells.forEach((cell) => titles.push(cell.textContent));
titles.join('\n');
'''