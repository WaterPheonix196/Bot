import jwt
import time
from typing import Optional, Dict, Any
from os import getenv
import aiohttp

class App:
    def __init__(self):
        self.app_id = getenv("GITHUB_APP_ID")
        self.installation_id = getenv("GITHUB_INSTALLATION_ID")
        self.private_key = getenv("GITHUB_PRIVATE_KEY")
        self._token: Optional[str] = None
        self._token_expires: Optional[float] = None

    async def _fetch(self, method: str, url: str, headers: Dict[str, str], **kwargs):
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, **kwargs) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                
                raise Exception(f"GitHub API error {resp.status}: {await resp.text()}")

    async def _get_token(self) -> str:
        if self._token and self._token_expires and time.time() < self._token_expires - 300:
            return self._token

        payload = {
            "iat": int(time.time()) - 60,
            "exp": int(time.time()) + 400,
            "iss": self.app_id,
        }

        jwt_token = jwt.encode(payload, self.private_key, algorithm="RS256")
        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"

        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        }

        data = await self._fetch("POST", url, headers)
        self._token = data["token"]
        self._token_expires = time.mktime(time.strptime(data["expires_at"], "%Y-%m-%dT%H:%M:%SZ"))
        
        return self._token

    async def get_commit_line_changes(self, owner: str, repo: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        try:
            token = await self._get_token()
            url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            }

            commit_data = await self._fetch("GET", url, headers)
            counts = {"added": 0, "removed": 0, "modified": 0}

            for f in commit_data.get("files", []):
                additions, deletions, status = f.get("additions", 0), f.get("deletions", 0), f.get("status", "")

                if status == "added":
                    counts["added"] += additions
                elif status == "removed":
                    counts["removed"] += deletions
                elif status in {"modified", "renamed"}:
                    modified = min(additions, deletions)
                    counts["modified"] += modified
                    counts["added"] += additions - modified
                    counts["removed"] += deletions - modified

            return counts
        except Exception as error:
            print(f"Error getting line change data: {error}")
            return None