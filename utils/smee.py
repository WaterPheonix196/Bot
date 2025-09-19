from aiohttp import ClientSession
from asyncio import sleep, create_task
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
        self._task = None
    
    def start_task(self):
        if not self._task or self._task.done():
            self._task = create_task(self._run())
        return self._task
    
    def stop_task(self):
        self._running = False

        if self._task and not self._task.done():
            self._task.cancel()

    async def _run(self):
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
                            if not line or line.startswith(":") or not line.startswith("data:"):
                                continue
                                
                            data_str = line[5:].strip()
                            try:
                                data = loads(data_str)
                                if data.get("x-github-event") == "push":
                                    body = data.get("body", {})
                                    payload_str = parse_qs(body).get("payload", [None])[0] if isinstance(body, str) else body.get("payload")
                                    
                                    if payload_str:
                                        await self._on_event(loads(payload_str))
                            except JSONDecodeError:
                                pass
            except:
                await sleep(5)

    def _calculate_file_types(self, payload: dict) -> str:
        all_changed_files = set()
        for commit in payload.get("commits", []):
            all_changed_files.update(commit.get("added", []) + commit.get("modified", []) + commit.get("removed", []))

        file_counts = {}
        for filename in all_changed_files:
            ext = filename.split('.')[-1] if '.' in filename else None
            if ext:
                file_counts[ext] = file_counts.get(ext, 0) + 1
        
        lang_map = {"kt": "Kotlin", "java": "Java", "py": "Python", "js": "JavaScript", "ts": "TypeScript", "json": "JSON", "gradle": "Gradle"}
        
        display_counts = {}
        other_count = 0
        for ext, count in file_counts.items():
            if ext in lang_map:
                display_counts[lang_map[ext]] = display_counts.get(lang_map[ext], 0) + count
            else:
                other_count += count
        
        if other_count > 0:
            display_counts["Other"] = other_count

        return ", ".join(f"{lang} ({count})" for lang, count in display_counts.items()) or "No files changed"

    async def _on_event(self, payload):
        try:
            repo = payload["repository"]
            head_commit = payload["head_commit"]
            
            repo_name = repo["name"]
            owner_name = repo["owner"]["login"]
            branch = payload["ref"].replace("refs/heads/", "")
            pusher_name = head_commit["author"]["name"]
            commit_message = head_commit["message"]
            sha_id = head_commit["id"]
            
            dt_object = datetime.fromisoformat(head_commit["timestamp"])
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
            embed.add_field(":bar_chart: Lines Changed", f"**`+{line_changes['added']}`** added\n**`-{line_changes['removed']}`** removed\n**`±{line_changes['modified']}`** modified")
            embed.add_field(":bulb: Details", f"Branch: {branch}\nTime: {time_utc}")
            embed.add_field(":file_folder: File Types", file_types_str)
            embed.add_field(":bust_in_silhouette: Author", pusher_name)
            
            await channel.send(content="<@&1392610508489621585>", embed=embed, role_mentions=True)
        except Exception as error:
            print(f"Error processing event: {error}")