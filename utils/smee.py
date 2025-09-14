from aiohttp import ClientSession
from asyncio import sleep
from json import JSONDecodeError, loads
from hikari import GatewayBot, GuildTextChannel, Embed
from urllib.parse import parse_qs
from datetime import datetime, timezone
from utils.github import App

class SmeeClient:
    
    def __init__(self, bot: GatewayBot, url: str):
        self.url = url
        self.bot = bot
        self._app = App()
        self._running = False
    
    async def start(self):
        self._running = True
        headers = {"Accept": "text/event-stream"}

        while self._running:
            try:
                async with ClientSession() as session:
                    async with session.get(self.url, headers=headers, timeout=None) as resp:
                        if resp.status != 200:
                            await sleep(5)
                            continue

                        async for line in resp.content:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data:"):
                                data_str = line[len("data:"):].strip()
                                try:
                                    data = loads(data_str)   

                                    if data.get("x-github-event") == "push":
                                        body = data.get("body", {})

                                        if isinstance(body, str):
                                            payload_str = parse_qs(body).get("payload", [None])[0]
                                        else:
                                            payload_str = body.get("payload")

                                        if not payload_str:
                                            return
                                        
                                        await self._on_event(loads(payload_str))
                                except JSONDecodeError:
                                    pass
                            elif not line or line.startswith(":"):
                                continue
            except:
                await sleep(5)

    def _calculate_file_types(self, payload: dict) -> str:
        file_counts = {}
        all_changed_files = set()
        for commit in payload.get("commits", []):
            all_changed_files.update(commit.get("added", []))
            all_changed_files.update(commit.get("modified", []))
            all_changed_files.update(commit.get("removed", []))

        for filename in all_changed_files:
            parts = filename.split('.')
            if len(parts) > 1:
                ext = parts[-1]
                file_counts[ext] = file_counts.get(ext, 0) + 1
        
        lang_map = {"kt": "Kotlin", "java": "Java", "py": "Python", "js": "JavaScript", "ts": "TypeScript", "json": "JSON", "gradle": "Gradle"}
        
        display_counts = {}
        other_count = 0
        for ext, count in file_counts.items():
            lang_name = lang_map.get(ext)
            if lang_name:
                display_counts[lang_name] = display_counts.get(lang_name, 0) + count
            else:
                other_count += count
        
        if other_count > 0:
            display_counts["Other"] = other_count

        file_types_str = " ".join(f"{lang} ({count})" for lang, count in display_counts.items())
        return file_types_str if file_types_str else "No files changed"

    async def _on_event(self, payload):
        try:
            repo_name = payload["repository"]["name"]
            branch = payload["ref"].replace("refs/heads/", "")
            pusher_name = payload["head_commit"]["author"]["name"]
            timestamp_str = payload["head_commit"]["timestamp"]
            commit_message = payload["head_commit"]["message"]
            owner_name = payload["repository"]["owner"]["login"]
            sha_id = payload["head_commit"]["id"]
            
            dt_object = datetime.fromisoformat(timestamp_str)
            time_utc = dt_object.astimezone(timezone.utc).strftime("%H:%M UTC")

            file_types_str = self._calculate_file_types(payload)
            line_changes = await self._app.get_commit_line_changes(owner_name, repo_name, sha_id)

            channel: GuildTextChannel = await self.bot.rest.fetch_channel("1392449172895957013")

            embed = Embed(
                title=f":rocket: New Commit to {repo_name}!",
                url=payload["compare"],
                color=0x0050a0
            )

            embed.add_field(":pencil: Commit Message", commit_message)
            embed.add_field(":bar_chart: Lines Changed", f"**`+{line_changes["added"]}`** added\n**`-{line_changes["removed"]}`** removed\n**`±{line_changes["modified"]}`** modified")
            embed.add_field(":bulb: Details", f"Branch: {branch}\nTime: {time_utc}")
            embed.add_field(":file_folder: File Types", file_types_str)
            embed.add_field(":bust_in_silhouette: Author", pusher_name)
            
            await channel.send(content="<@&1392610508489621585>", embed=embed, role_mentions=True)
        except Exception as e:
            print(f"Error processing GitHub push event: {e}")


    async def stop(self):
        self._running = False