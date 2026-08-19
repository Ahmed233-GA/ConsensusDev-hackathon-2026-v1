import requests

resp = requests.post("http://localhost:8000/webhook", json={
    "pr_number": 101,
    "repo_name": "my-org/my-repo",
    "title": "Add user auth endpoint",
    "diff_text": (
        "diff --git a/app.py b/app.py\n"
        "+ API_KEY = \"sk-12345\"\n"
        "+ def login(user, pw):\n"
        "+     query = \"SELECT * FROM users WHERE name='\" + user + \"'\""
    ),
})
print(resp.json())