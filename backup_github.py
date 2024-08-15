#!/usr/bin/env python3

# Backup all of your repos from github

# Use Github API to get list of repo urls, then clone them all
#   finally, package it all up in a gzipped tarfile named like: archives/Github_Repos_2024-08-14_190009.tar.gz

# NOTE: do not use zip, cannot handle symlinks and drops file attributes

import requests
import time
import subprocess
import sys
import os
import tarfile
import shutil

from pathlib import Path
from datetime import datetime
from traceback import format_exc

from config_github import GITHUB_USERNAME, AUTH_TOKEN

REPOS_API_ENDPOINT = f'https://api.github.com/users/{GITHUB_USERNAME}/repos'

TIME_BETWEEN_PAGES = 0.25

TARGET_DIR = Path().cwd().joinpath('repos')
ARCHIVES_DIR = Path().cwd().joinpath('archives')


def get_json_url(url: str, headers: dict, params: dict):
    """Get json data returned from a url endpoint"""
    resp = requests.get(url=url, headers=headers, params=params)
    data = resp.json()
    return data


def get_paged_data(url: str, headers: dict) -> list:
    """Fetch all pages for the given request"""
    print(f'Fetching all pages for endpoint: {url}')
    params = {
        'page': 1,
        'per_page': 50
    }
    this_page = get_json_url(url=url, headers=headers, params=params)
    all_data = []
    while len(this_page) > 0:
        if 'error' in this_page:
            print(f'Encountered an error: {this_page["error"]}: {this_page["error_description"]}')
            break
        for entry in this_page:
            all_data.append(entry)
        print(f'    Processed page: {params["page"]}, currently have {len(all_data)} items')
        params["page"] += 1
        time.sleep(TIME_BETWEEN_PAGES)
        this_page = get_json_url(url=url, headers=headers, params=params)
    print(f'    Fetched {len(all_data)} results in {params["page"] - 1} pages')
    return all_data


def get_project_urls() -> list[str]:
    """
    Get a list of project urls
    """
    print('Fetching all repo urls....')
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = get_paged_data(url=REPOS_API_ENDPOINT, headers=headers)

    urls = []

    for entry in data:
        urls.append(entry['clone_url'])
    print(f'Found {len(urls)} repos')
    return urls


def clone_a_repo(url: str, within: Path) -> None:
    """Clone given repo to target folder"""
    # NOTE: we send all output to /dev/null, so we rely on exception handling since we cannot see output
    try:
        subprocess.run(f'git clone {url}', shell=True, check=True, cwd=str(within), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print(f'Failed to clone: {url}')
        sys.exit(1)


def clone_these_repos(url_list: list[str], within: Path, limit=0) -> None:
    """Clone a list of repos to target folder"""
    count = 0
    for this_url in url_list:
        count += 1
        print(f'Cloning repo {count}: {this_url}')
        clone_a_repo(url=this_url, within=within)
        if limit > 0:
            if count >= limit:
                break


def get_timestamp() -> str:
    """Get a string timestamp for filename"""
    return datetime.now().strftime('%Y-%m-%d_%H%M%S')


def create_targz(source_dir: Path, output_filename: str):
    """Create a gzipped tarfile with the contents of the given folder
        will not include the folder itself
    """
    print(f'Creating targz: {str(output_filename)} from folder: {str(source_dir)}')
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(str(source_dir), arcname='.')


if __name__ == '__main__':
    try:
        # cleanup any failed previous attempt
        if TARGET_DIR.exists():
            print('Removing existing local repos copy')
            shutil.rmtree(str(TARGET_DIR))
        TARGET_DIR.mkdir()

        # ensure archives folder exists
        ARCHIVES_DIR.mkdir(exist_ok=True)

        # fetch list of all repo urls
        all_urls = get_project_urls()

        # clone all repos
        clone_these_repos(all_urls, TARGET_DIR)

        # create a zip archive of all the cloned repos
        timestamp = get_timestamp()
        out_filename = ARCHIVES_DIR.joinpath(f'Github_Repos_{timestamp}.tar.gz')
        create_targz(TARGET_DIR, out_filename)

        # cleanup the cloned repos
        # NOTE: in the case of "rm -rf thisfolder" or "shutil.rmtree(thisfolder)", symlinks are NOT followed
        #   so if you delete a folder that contains symlinks to thinks outside that folder, those thinks will not be deleted
        shutil.rmtree(str(TARGET_DIR))

        print(f'Backup Success! Output: {str(out_filename)}')
    except BaseException as ex:
        print(f'An unexpected exception was encountered: {ex}')
        print(format_exc(ex))
        sys.exit(1)
