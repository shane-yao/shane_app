import asyncio
from daily_note import DailyNote
from joplin import JoplinClipperServerEndpoint, JoplinDataAPI

class Application:
    def __init__(self) -> None:
        clipper_ep = JoplinClipperServerEndpoint(self)
        self._joplin_api = JoplinDataAPI(clipper_ep)

    def run(self) -> None:
        asyncio.run(self.async_run())
    
    async def async_run(self) -> None:
        try:
            await self._joplin_api.initialize()
            self._joplin_api.dump()
            notes = await self._joplin_api.get_folder_notes_with_path("MyLog/Daily")
            for one_note in notes:
                daily_note = DailyNote()
                daily_note.set_content(one_note.body)
                
        finally:
            await self.do_cleanup()

    async def do_cleanup(self) -> None:
        await self._joplin_api.close()