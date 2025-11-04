import aiohttp, asyncio
from http import HTTPStatus
from urllib.parse import urlsplit, urljoin

FOLDER_SEP = "/"
GLOBAL_MAX_PAGES = 100

class ResourceObject(object):
    def __init__(self) -> None:
        self.id = ""
        self.title = None

    def fill_data(self, data_dict):
        self.id = data_dict["id"]
        self.title = data_dict["title"]

class Note(ResourceObject):
    def __init__(self) -> None:
        super().__init__()
        self.parent_id = None
        self.body = None

    def fill_data(self, data_dict):
        super().fill_data(data_dict)
        self.parent_id = data_dict["parent_id"]
        self.body = data_dict.get("body", None)

class Folder(ResourceObject):
    def __init__(self) -> None:
        super().__init__()
        self.parent = None
        self.sub_folders = list()
        self.sub_folders_by_name = dict()
        self.notes = list()

    def fill_data(self, data_dict):
        super().fill_data(data_dict)
        self.parent_id = data_dict["parent_id"]

    def __hash__(self) -> int:
        return hash(self.id)
    
    def add_child(self, child_folder):
        self.sub_folders.append(child_folder)
        self.sub_folders_by_name[child_folder.title] = child_folder
        child_folder.parent = self
        
    def add_note(self, note):
        self.notes.append(note)

class FolderHierarchy(object):
    def __init__(self) -> None:
        self._root = Folder()
        self._root.title = "*ROOT*"
        self._folder_by_guid = dict()

    def get_folder(self, id, create_stub=True):
        if id == "":
            return self._root
        
        folder = self._folder_by_guid.get(id)
        if folder is None and create_stub:
            folder = Folder()
            folder.id = id
            folder.title = "*AUTO_STUB*"
            self._folder_by_guid[id] = folder
        return folder

    def add_folder_data(self, folder_data):
        new_folder_id = folder_data["id"]
        new_folder = self.get_folder(new_folder_id)
        new_folder.fill_data(folder_data)
        parent_folder = self.get_folder(new_folder.parent_id)
        parent_folder.add_child(new_folder)
        return new_folder
    
    def dump_folder(self, folder, indent=1):
        print("\t" * (indent - 1), "[%s]" % folder.title)
        for one_note in folder.notes:
            print("\t" * indent, one_note.title)
        for sub_folder in folder.sub_folders:
            self.dump_folder(sub_folder, indent + 1)
        
    def dump(self):
        self.dump_folder(self._root)

    def get_folder_with_path(self, folder_path):
        split_path = folder_path.split(FOLDER_SEP)
        current_folder = self._root
        found = True
        for folder_entry in split_path:
            current_folder = current_folder.sub_folders_by_name.get(folder_entry)
            if current_folder is None:
                found = False
                break
        if found:
            return current_folder
        else:
            return None

        
class JoplinClipperServerEndpoint(object):
    def __init__(self, aio_http_client) -> None:
        self._base_url = "http://localhost"
        self._port = None
        # TODO Test token
        self._auth_token = None
        self._port_probe_range = range(41184, 41194)
        self._client = aio_http_client
        self._sys_url = {
            "auth": "auth",
            "auth_check": "auth/check",
            "ping": "ping",
        }

    async def initialize(self):
        self._client = aiohttp.ClientSession()
        await self.probe_url()
        await self.check_auth()
        if self._auth_token is None:
            return False
        return True
    
    async def get_note(self, id, fields=None):
        query_params = dict()
        if fields is not None:
            query_params["fields"] = ",".join(fields)

        return await self.api_request("GET", "/notes/%s" % id, query_params=query_params)
    
    async def get_folders(self, page=1):
        return await self.api_request("GET", "/folders", query_params={
            "page": page
        })
    
    async def get_folders_notes(self, folder_id, page=1):
        return await self.api_request("GET", "/folders/%s/notes" % folder_id, query_params={
            "page": page
        })

    def get_sys_url(self, method):
        return urljoin(self._base_url, self._sys_url[method])


    async def api_request(self, method, uri, json_data=None, headers=None, query_params=None, timeout=10, need_token=True):
        if self._client is None:
            return HTTPStatus.INTERNAL_SERVER_ERROR, None
        
        if need_token:
            if query_params is None:
                query_params = {
                    "token": self._auth_token
                }
            else:
                query_params["token"] = self._auth_token
        try:                
            async with self._client.request(method, urljoin(self._base_url, uri), json=json_data, headers=headers, timeout=timeout, params=query_params) as resp:
                status = resp.status
                json_resp = await resp.json()
        except Exception as e:
            return HTTPStatus.BAD_REQUEST, None
        return status, json_resp


    async def check_auth(self):
        if self._auth_token is not None:
            return
        
        status, resp = await self.api_request("POST", self.get_sys_url("auth"), need_token=False)
        auth_token = resp.get("auth_token")
        print("Waiting for authorize.")
        while True:
            http_status, resp = await self.api_request("GET", self.get_sys_url("auth_check"), query_params={
                "auth_token": auth_token
            }, need_token=False)
            
            status = resp.get("status")
            if status == "rejected":
                raise RuntimeError("Client reject authorized")
            elif status == "accepted":
                self._auth_token = resp.get("token")
                print("Auth successed")
                break
            elif status == "waiting":
                print("Still waiting.....")
                await asyncio.sleep(1)
                continue
            else:
                raise RuntimeError("Unknow query status:" + str(status))
            
    async def probe_url(self):
        base_url_parse = urlsplit(self._base_url)
        hostname = base_url_parse.hostname
        for i in self._port_probe_range:
            # Change port to probe
            base_url_parse = base_url_parse._replace(netloc=(hostname + ":%s" % i))
            new_port_url = base_url_parse.geturl()
            ping_url = urljoin(new_port_url, "ping")
            print(ping_url)
            try:
                resp = await self._client.get(ping_url)
                content = await resp.text()
                if (content == "JoplinClipperServer"):
                    self._base_url = new_port_url
                    break
            except:
                print("Probe failed, try next port")

        print("probeURL:", self._base_url)
        
    async def close(self):
        session_to_destroy = self._client
        self._client = None
        await session_to_destroy.close()
        await asyncio.sleep(0.25)

class JoplinDataAPI(object):
    def __init__(self, endpoint) -> None:
        self.resources = dict()
        self.folders = FolderHierarchy()
        self.notes = dict()
        self._endpoint = endpoint

    async def initialize(self):
        if await self._endpoint.initialize() is False:
            return False
        
        await self.fetch_folders()
        await self.fetch_folders_notes()

    async def close(self):
        await self._endpoint.close()

    async def fetch_folders(self):
        page = 1
        all_folders = list()
        while True:
            if page > GLOBAL_MAX_PAGES:
                print("Max pages exceed, consider change GLOBAL_MAX_PAGES")
                break

            status, ret_obj = await self._endpoint.get_folders(page)
            if status != 200:
                break
            items = ret_obj["items"]
            all_folders.extend(items)
            has_more = ret_obj["has_more"]
            if not has_more:
                break
            page += 1
        for new_folder_data in all_folders:
            res_folder = self.folders.add_folder_data(new_folder_data)
            self.add_resource(res_folder)

    def create_note(self, note_data):
        new_note = Note()
        new_note.fill_data(note_data)
        self.resources[new_note.id] = new_note
        self.notes[new_note.id] = new_note
        return new_note

    def add_resource(self, res):
        self.resources[res.id] = res

    async def fetch_folders_notes(self, current_foler=None):
        if current_foler is None:
            current_foler = self.folders._root
        if current_foler.id is not None:
            note_data_list = await self._get_folder_notes(current_foler.id)
            for one_note_data in note_data_list:
                new_note = self.create_note(one_note_data)
                current_foler.add_note(new_note)

        for sub_folder in current_foler.sub_folders:
            await self.fetch_folders_notes(sub_folder)
        
    async def _get_folder_notes(self, folder_id):
        page = 1
        all_notes = list()
        while True:
            if page > GLOBAL_MAX_PAGES:
                print("Max pages exceed, consider change GLOBAL_MAX_PAGES")
                break
            status, ret_obj = await self._endpoint.get_folders_notes(folder_id)
            if status != 200:
                break
            items = ret_obj["items"]
            all_notes.extend(items)
            has_more = ret_obj["has_more"]
            if not has_more:
                break
            page += 1
        return all_notes
    
    async def get_folder_notes_with_path(self, path):
        folder = self.folders.get_folder_with_path(path)
        if folder is None:
            return None
        for one_note in folder.notes:
            status, note_data = await self._endpoint.get_note(one_note.id, ["id", "parent_id", "title", "body"])
            # TODO Check status
            one_note.fill_data(note_data)

        return folder.notes
    
    def dump(self):
        self.folders.dump()