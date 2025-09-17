import jwt
import time
from typing import Optional, Dict, Any
from constants import GITHUB_APP_ID, GITHUB_INSTALLATION_ID, GITHUB_PRIVATE_KEY
import aiohttp

class App:
    def __init__(self):
        self.app_id = GITHUB_APP_ID
        self.installation_id = GITHUB_INSTALLATION_ID
        self.private_key = GITHUB_PRIVATE_KEY
        self._token = None
        self._token_expires = None

    async def _get_token(self) -> str:
        if self._token and self._token_expires and time.time() < self._token_expires - 300:
            return self._token
        
        payload = {
            "iat": int(time.time()) - 60,
            "exp": int(time.time()) + 400,
            "iss": self.app_id
        }
        
        jwt_token = jwt.encode(payload, self.private_key, algorithm="RS256")
        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                if response.status == 201:
                    data = await response.json()
                    self._token = data["token"]
                    self._token_expires = time.time() + 3600
                    return self._token
                else:
                    raise Exception(f"Failed to get token")

    async def get_commit_line_changes(self, owner: str, repo: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        try:
            token = await self._get_token()
            url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return None
                    
                    commit_data = await response.json()
            
            pure_additions = 0
            pure_deletions = 0
            modified_lines = 0
            
            for file_data in commit_data.get("files", []):
                status = file_data.get("status", "")
                additions = file_data.get("additions", 0)
                deletions = file_data.get("deletions", 0)
                
                if status == "added":
                    pure_additions += additions
                elif status == "removed":
                    pure_deletions += deletions
                elif status in ["modified", "renamed"]:
                    modified_count = min(additions, deletions)
                    modified_lines += modified_count
                    pure_additions += additions - modified_count
                    pure_deletions += deletions - modified_count
            
            return {
                "added": pure_additions,
                "removed": pure_deletions,
                "modified": modified_lines,
            }
            
        except Exception as e:
            print(f"Error getting commit data")
            return None