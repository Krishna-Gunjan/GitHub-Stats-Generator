from flask import Flask, render_template, request
import requests
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

app = Flask(__name__)

# Define headers for requests (GitHub Token if available)
token = ""  # Optional, but recommended
headers = {'Authorization': f'token {token}'} if token else {}

def fetch_user_info(username: str) -> Optional[Dict[str, str]]:
    url = f'https://api.github.com/users/{username}'
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def fetch_repos(username: str) -> List[Dict[str, str]]:
    repos = []
    url = f'https://api.github.com/users/{username}/repos'
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repos.extend(response.json())
            url = response.links.get('next', {}).get('url', None)
        else:
            break
    return repos

def fetch_events(username: str) -> List[Dict[str, str]]:
    events = []
    url = f'https://api.github.com/users/{username}/events'
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            events.extend(response.json())
            url = response.links.get('next', {}).get('url', None)
        else:
            break
    return events

def calculate_contributions(events: List[Dict[str, str]]) -> Tuple[int, int]:
    contributions_last_year = 0
    total_contributions = 0
    today = datetime.now()
    one_year_ago = today - timedelta(days=365)
    
    for event in events:
        event_date = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        if event_date >= one_year_ago:
            contributions_last_year += 1
        total_contributions += 1
    
    return contributions_last_year, total_contributions

def fetch_repo_stats(repos: List[Dict[str, str]]) -> Tuple[int, int, int, int, Dict[str, float]]:
    stars = commits = pull_requests = issues = 0
    languages = defaultdict(int)
    for repo in repos:
        stars += repo['stargazers_count']
        commits += fetch_commit_count(repo['full_name'])
        pull_requests += fetch_pull_request_count(repo['full_name'])
        issues += fetch_issue_count(repo['full_name'])
        for lang, count in fetch_languages(repo['full_name']).items():
            languages[lang] += count
    
    total_langs = sum(languages.values())
    languages_percentage = {lang: (count / total_langs) * 100 for lang, count in languages.items()}
    
    return stars, commits, pull_requests, issues, languages_percentage

def fetch_commit_count(repo_full_name: str) -> int:
    url = f'https://api.github.com/repos/{repo_full_name}/commits'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        commit_count = len(response.json())
        while 'next' in response.links:
            response = requests.get(response.links['next']['url'], headers=headers)
            commit_count += len(response.json())
        return commit_count
    return 0

def fetch_pull_request_count(repo_full_name: str) -> int:
    url = f'https://api.github.com/repos/{repo_full_name}/pulls?state=all'
    response = requests.get(url, headers=headers)
    return len(response.json()) if response.status_code == 200 else 0

def fetch_issue_count(repo_full_name: str) -> int:
    url = f'https://api.github.com/repos/{repo_full_name}/issues?state=all'
    response = requests.get(url, headers=headers)
    return len(response.json()) if response.status_code == 200 else 0

def fetch_languages(repo_full_name: str) -> Dict[str, int]:
    url = f'https://api.github.com/repos/{repo_full_name}/languages'
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {}

def fetch_streaks(username: str) -> Tuple[int, int]:
    # Placeholder function. Implement logic to fetch streaks if necessary
    current_streak = 0
    longest_streak = 0
    return current_streak, longest_streak

def fetch_achievements(username: str) -> int:
    # Placeholder function. Implement logic to fetch achievements if necessary
    achievements = 0
    return achievements

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats', methods=['POST'])
def stats():
    username = request.form['username']
    user_info = fetch_user_info(username)
    repos = fetch_repos(username)
    events = fetch_events(username)
    
    if user_info:
        profile_name = user_info.get('name', 'N/A')
        followers_count = user_info.get('followers', 0)
        following_count = user_info.get('following', 0)
        stars, commits, pull_requests, issues, languages_percentage = fetch_repo_stats(repos)
        contributions_last_year, total_contributions = calculate_contributions(events)
        current_streak, longest_streak = fetch_streaks(username)
        achievements = fetch_achievements(username)
        
        return render_template('stats.html', 
                               profile_name=profile_name,
                               followers_count=followers_count,
                               following_count=following_count,
                               stars=stars,
                               commits=commits,
                               pull_requests=pull_requests,
                               issues=issues,
                               contributions_last_year=contributions_last_year,
                               total_contributions=total_contributions,
                               current_streak=current_streak,
                               longest_streak=longest_streak,
                               achievements=achievements,
                               languages_percentage=languages_percentage)
    else:
        return "Error: Could not retrieve user info"

if __name__ == '__main__':
    app.run(debug=True)
