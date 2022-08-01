from pprint import pprint
import re
import requests
from itertools import groupby
from operator import itemgetter
import csv
import urllib.parse


ALLOWED_EXT = {'mp4', 'mkv'}
REJECTED_EXT = {'srt'}

SKIP_REGEX = r'.*(trailer|Trailer).*'


def scan_node(url):
    links_regex = r'<a href="([^.][^\"]+)">[^<]+</a>'
    response = requests.get(url)
    if response.status_code != 200:
        pprint(response.status_code)
    content = response.text
    links = re.findall(links_regex, content)
    return links

with open('./dir_list.txt', 'r', encoding='UTF-8') as dir_list:
    todo_list = dir_list.readlines()

todo = [
    todo_item.strip()
    for todo_item in todo_list[:-1]
]

completed = []
matches = []
mismatches = []
unknown = []

matched_dirs = []

max_visited = 100000

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

dir_output = [
    [
        re.sub(r'[^A-Za-z0-9:-]+', ' ', urllib.parse.unquote(word))
        for word in match.split('/')
        if word not in ('', 'https:', 'http:')
    ]
    for match in matches
]

dir_output_sorted = sorted(dir_output, key=itemgetter(0))
dir_output_grouped = groupby(dir_output_sorted, key=itemgetter(0))
for k, g in dir_output_grouped:
    suffix = re.sub(r' +', '_', k)
    print(f'writing out {suffix}')
    with open(f'dir_output_{suffix}.csv', 'w', newline='', encoding='UTF-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(g)

'''
cells = document.querySelectorAll('tr td:nth-child(2)');
titles = [];
cells.forEach((cell) => titles.push(cell.textContent));
titles.join('\n');
'''