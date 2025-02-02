import praw

# Reddit API credentials
reddit = praw.Reddit(
    client_id="your_client_id",
    client_secret="your_client_secret",
    username="your_username",
    password="your_password",
    user_agent="script:reddit_flair_bot:v1.0 (by u/your_username)"
)

# Get subreddit
subreddit = reddit.subreddit("FindAUnit")

# Fetch available flairs
for flair in subreddit.flair.link_templates:
    print(f"Flair ID: {flair['id']}, Flair Text: {flair['text']}")