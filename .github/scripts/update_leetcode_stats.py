import re
import sys

import requests

LEETCODE_USERNAME = "EN11uuIKBm"
LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": f"https://leetcode.com/{LEETCODE_USERNAME}/",
    "User-Agent": "Mozilla/5.0 (compatible; GitHub-Actions-Bot)",
}


def fetch_user_stats(username):
    query = """
    query getUserStats($username: String!) {
        matchedUser(username: $username) {
            submitStats: submitStatsGlobal {
                acSubmissionNum {
                    difficulty
                    count
                }
            }
        }
    }
    """
    payload = {"query": query, "variables": {"username": username}}
    response = requests.post(
        LEETCODE_GRAPHQL_URL, json=payload, headers=HEADERS, timeout=30
    )
    response.raise_for_status()
    return response.json()


def fetch_contest_stats(username):
    query = """
    query getUserContestRanking($username: String!) {
        userContestRanking(username: $username) {
            rating
            globalRanking
            topPercentage
            totalParticipants
        }
    }
    """
    payload = {"query": query, "variables": {"username": username}}
    response = requests.post(
        LEETCODE_GRAPHQL_URL, json=payload, headers=HEADERS, timeout=30
    )
    response.raise_for_status()
    return response.json()


def get_problems_solved(stats_data):
    try:
        submissions = (
            stats_data["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]
        )
        for entry in submissions:
            if entry["difficulty"] == "All":
                return entry["count"]
    except (KeyError, TypeError):
        pass
    return None


def get_contest_info(contest_data):
    try:
        ranking = contest_data["data"]["userContestRanking"]
        if ranking is None:
            return None, None
        rating = round(ranking["rating"])
        top_pct = ranking["topPercentage"]
        return rating, top_pct
    except (KeyError, TypeError):
        pass
    return None, None


def update_readme(rating, problems_solved, top_percentage):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Replace contest rating value in the badge URL
    content = re.sub(
        r"(https://img\.shields\.io/badge/Contest%20Rating-)[0-9]+(-FFA116)",
        rf"\g<1>{rating}\g<2>",
        content,
    )

    # Replace problems solved value in the badge URL (preserve trailing +)
    content = re.sub(
        r"(https://img\.shields\.io/badge/Problems%20Solved-)[0-9]+%2B(-36BCF7)",
        rf"\g<1>{problems_solved}%2B\g<2>",
        content,
    )
    # Also handle un-encoded + sign variant
    content = re.sub(
        r"(https://img\.shields\.io/badge/Problems%20Solved-)[0-9]+\+(-36BCF7)",
        rf"\g<1>{problems_solved}+\g<2>",
        content,
    )

    # Replace top percentage value in the badge URL (%25 is URL-encoded %)
    top_pct_str = f"{top_percentage:.2f}%25"
    content = re.sub(
        r"(https://img\.shields\.io/badge/Top-)[0-9]+(?:\.[0-9]+)?%25(-brightgreen)",
        rf"\g<1>{top_pct_str}\g<2>",
        content,
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print(f"Fetching LeetCode stats for username: {LEETCODE_USERNAME}")

    # Fetch user stats (problems solved)
    try:
        stats_data = fetch_user_stats(LEETCODE_USERNAME)
    except requests.RequestException as e:
        print(f"Error fetching user stats: {e}", file=sys.stderr)
        sys.exit(1)

    problems_solved = get_problems_solved(stats_data)
    if problems_solved is None:
        print("Warning: Could not parse problems solved count.", file=sys.stderr)
        sys.exit(1)

    # Fetch contest ranking stats
    try:
        contest_data = fetch_contest_stats(LEETCODE_USERNAME)
    except requests.RequestException as e:
        print(f"Error fetching contest stats: {e}", file=sys.stderr)
        sys.exit(1)

    rating, top_percentage = get_contest_info(contest_data)
    if rating is None or top_percentage is None:
        print("Warning: Could not parse contest ranking data.", file=sys.stderr)
        sys.exit(1)

    print(f"  Contest Rating  : {rating}")
    print(f"  Problems Solved : {problems_solved}")
    print(f"  Top Percentage  : {top_percentage:.2f}%")

    update_readme(rating, problems_solved, top_percentage)
    print("README.md updated successfully.")


if __name__ == "__main__":
    main()
