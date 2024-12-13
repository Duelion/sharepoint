from typing import Optional, Any, Type, TypeVar

import requests
from pydantic.v1 import BaseModel
from pydantic.v1 import root_validator, Field

from . import sp_fields
from .models import TokenData
from .session import SharepointSession
from .utils import replace_string_map, replace_key_mapping, to_camel, COLUMN_ESCAPE, AUTO_LIST_FIELDS, \
    AUTO_ITEM_PROPERTIES

HEADERS = {"accept": "application/json;odata=verbose", "content-type": "application/json;odata=verbose",
           "IF-MATCH": "*"}


class SharePoint:

    def __init__(self, client_id: str, tenant_id: str, secret: str, domain: str, site: str,
                 session: requests.Session = None):
        self.site = site
        self.domain = domain
        self.secret = secret
        self.client_id = client_id
        self.tenant_id = tenant_id
        self._session = session if session is not None else SharepointSession()
        self._access_token: Optional[TokenData] = None
        self._session.headers.update(HEADERS)

    @property
    def client_id_data(self):
        return f"{self.client_id}@{self.tenant_id}"

    @property
    def resource(self):
        return f"00000003-0000-0ff1-ce00-000000000000/{self.domain}@{self.tenant_id}"

    @property
    def access_token(self):
        token_data = self._access_token
        if token_data is None or token_data.is_expired():
            token_data = self.get_auth_token()
        return token_data

    @property
    def session(self):
        token = {"Authorization": f"Bearer {self.access_token.access_token}"}
        self._session.headers.update(token)
        return self._session

    @property
    def api(self):
        return f"https://puentesur.sharepoint.com/sites/{self.site}/_api/web"

    def get_folder(self, path: str):
        url = self.api + f"/GetFolderByServerRelativeUrl('{path}')"
        response = self.session.get(url)
        data = response.json()['d']
        folder = Folder(**data, sharepoint=self)
        return folder

    @property
    def root_folder(self):
        return self.get_folder('Shared Documents')

    def get_auth_token(self):
        url = f"https://login.microsoftonline.com/{self.tenant_id}/tokens/oAuth/2"
        data = {"grant_type": "client_credentials",
                "client_id": self.client_id_data,
                "client_secret": self.secret,
                "resource": self.resource}

        response = requests.get(url, data=data)
        token_json = response.json()
        expire_in = int(token_json["expires_in"])
        access_token = token_json["access_token"]
        token_data = TokenData(expire_in=expire_in, access_token=access_token)
        return token_data



    def get_list(self, title):
        url = self.api + f"/lists/GetByTitle('{title}')"
        response = self.session.get(url)
        data = response.json()["d"]
        list_ = List(**data, sharepoint=self)
        return list_

    def get_all_lists(self):
        url = self.api + f"/lists/?$filter=Hidden eq false and IsCatalog eq false"
        response = self.session.get(url)
        data = response.json()["d"]
        results = data["results"]
        lists = [List(**list_, sharepoint=self) for list_ in results]
        return lists

    def create_list(self, name, description=None, document_library=False, title_field_not_required=True):
        url = self.api + "/lists"
        base_template = 101 if document_library else 100  # Lista normal o con archivos adjuntos
        payload = {
            "__metadata": {
                "type": "SP.List"
            },
            "AllowContentTypes": True,
            "BaseTemplate": base_template,
            "ContentTypesEnabled": True,
            "Title": name
        }
        if description is not None:
            payload["Description"] = description
        response = self.session.post(url, json=payload)
        data = response.json()["d"]
        list_ = List(**data, sharepoint=self)
        if title_field_not_required:
            title_field = list_.get_field_by_static_name("Title")
            title_field.update({"Required": False})
        return list_


    def create_list_from_xml(self, name, xml, description=None, document_library=False, title_field_not_required=True):
        url = self.api + "/lists"
        base_template = 101 if document_library else 100  # Lista normal o con archivos adjuntos
        payload = {
            "__metadata": {
                "type": "SP.List"
            },
            "AllowContentTypes": True,
            "BaseTemplate": base_template,
            "ContentTypesEnabled": True,
            "Title": name
        }
        if description is not None:
            payload["Description"] = description
        response = self.session.post(url, json=payload)
        data = response.json()["d"]
        list_ = List(**data, sharepoint=self)
        if title_field_not_required:
            title_field = list_.get_field_by_static_name("Title")
            title_field.update({"Required": False})
        return list_


GenericModel = TypeVar('GenericModel', bound=BaseModel)


class BaseSharePointModel(BaseModel):
    deferred: dict[str, str] = Field(..., repr=False)
    uri: str
    type: str
    sharepoint: SharePoint = Field(..., repr=False)

    class Config:
        alias_generator = to_camel
        arbitrary_types_allowed = True

    @root_validator(pre=True)
    def construct_values(cls, values: dict):
        result = {}
        values["Sharepoint"] = values.pop("sharepoint")
        values["Uri"] = values["__metadata"]["uri"]
        values["Type"] = values["__metadata"]["type"]
        for key, value in values.items():
            try:
                deferred = value["__deferred"]
                uri = deferred["uri"]
            except (TypeError, KeyError):
                continue
            result[key] = uri
        values["Deferred"] = result
        return values

    def get_deferred_item(self, deferred_field: str, model: Type[GenericModel], params: dict = None) -> GenericModel:
        params = {} if params is None else params
        url = self.deferred[deferred_field]
        response = self.sharepoint.session.get(url, params=params)
        data = response.json()["d"]
        result = model(**data, sharepoint=self.sharepoint)
        return result

    def get_deferred_items(self, deferred_field: str, model: Type[GenericModel], params: dict = None) -> list[
        GenericModel]:
        params = {} if params is None else params
        url = self.deferred[deferred_field]
        response = self.sharepoint.session.get(url, params=params)
        results = []
        data = response.json()["d"]
        results.extend(data["results"])
        while next_url := data.get("__next"):
            response = self.sharepoint.session.get(next_url)
            data = response.json()["d"]
            results.extend(data["results"])
        items = [model(**item, sharepoint=self.sharepoint) for item in results]
        return items


class File(BaseSharePointModel):
    name: str
    time_created: str

    def download(self):
        url = self.uri + "/$value"
        file_data = self.sharepoint.session.get(url)
        return file_data.content

    @property
    def list_item(self):
        item = self.get_deferred_item(deferred_field='ListItemAllFields', model=Item)
        return item


class Folder(BaseSharePointModel):
    name: str
    time_created: str
    item_count: int
    server_relative_url: str

    @property
    def files(self) -> list[File]:
        items = self.get_deferred_items("Files", File)
        return items

    @property
    def folders(self) -> list["Folder"]:
        items = self.get_deferred_items("Folders", Folder)
        return items

    def upload_file(self, file_name, content) -> File:
        url = self.uri + f"/Files/add(url='{file_name}',overwrite=true)"
        response = self.sharepoint.session.post(url, data=content)
        file = response.json()["d"]
        return File(**file, sharepoint=self.sharepoint)

    def get_file(self, name: str) -> File:
        files = self.files
        for file in files:
            if file.name == name:
                return file
        raise KeyError(f"File with name {name} not found.")

    def create_folder(self, name: str):
        url = self.sharepoint.api + "/folders"
        data = {"__metadata": {"type": "SP.Folder"},
                "ServerRelativeUrl": f"{self.server_relative_url}/{name}"
                }
        response = self.sharepoint.session.post(url, json=data)
        data = response.json()["d"]
        folder = Folder(**data, sharepoint=self.sharepoint)
        return folder



class Item(BaseSharePointModel):
    id: int
    properties: dict[str, Any] = Field(..., alias="__UserCreatedProperties")

    @root_validator(pre=True)
    def properties_user_created(cls, values: dict):
        result = {}
        for key, value in values.items():
            if key not in AUTO_ITEM_PROPERTIES:
                key = replace_string_map(key, COLUMN_ESCAPE, reverse=True)
                result[key] = value
        values["__UserCreatedProperties"] = result
        return values

    @property
    def file(self):
        item = self.get_deferred_item("File", File)
        return item

    def update(self, data) -> None:
        data = replace_key_mapping(data, COLUMN_ESCAPE)
        payload = {**data,
                   "__metadata": {"type": self.type}
                   }
        self.sharepoint.session.patch(self.uri, json=payload)

    def delete(self):
        self.sharepoint.session.delete(self.uri)


class ListField(BaseSharePointModel):
    static_name: str
    title: str
    internal_name: str
    description: str
    required: bool
    hidden: bool
    default_value: Any
    custom_formatter: Optional[str]
    field_type: str = Field(..., alias="TypeAsString")

    def update(self, data) -> None:
        data = replace_key_mapping(data, COLUMN_ESCAPE)
        payload = {**data,
                   "__metadata": {"type": self.type}
                   }
        self.sharepoint.session.patch(self.uri, json=payload)


class List(BaseSharePointModel):
    id: str
    title: str
    item_count: int
    hidden: bool
    entity_type: str = Field(..., alias="ListItemEntityTypeFullName")
    base_template: int

    @property
    def folder(self) -> Folder:
        folder = self.get_deferred_item("RootFolder", Folder)
        return folder

    @property
    def fields(self) -> list[ListField]:
        items = self.get_deferred_items("Fields", ListField)
        return items

    @property
    def items(self) -> list[Item]:
        items = self.get_deferred_items("Items", Item)
        return items

    def get_user_created_fields(self) -> list[ListField]:
        items = self.fields
        items = [field for field in items if field.static_name not in AUTO_LIST_FIELDS]
        return items

    def get_field_by_static_name(self, static_name):
        fields = self.fields
        fields = [field for field in fields if field.static_name == static_name]
        if not fields:
            raise KeyError(f"No field found with static_name: {static_name}")
        return fields[0]

    def create_field(self, payload):
        url = self.uri + "/fields"
        url = url + "/addfield" if payload.get("parameters") else url
        response = self.sharepoint.session.post(url, json=payload)
        data = response.json()["d"]
        return data

    def create_item(self, data) -> Item:
        url = self.uri + "/items"
        data = replace_key_mapping(data, COLUMN_ESCAPE)
        payload = {**data,
                   "__metadata": {"type": self.entity_type}}
        response = self.sharepoint.session.post(url, json=payload)
        data = response.json()["d"]
        item = Item(**data, sharepoint=self.sharepoint)
        return item

    def upload_file(self, file_name, content, data=None):
        file = self.folder.upload_file(file_name, content)
        if data is not None:
            file.list_item.update(data)
        return file

    def delete(self):
        self.sharepoint.session.delete(self.uri)


    def query_items(self, filters: list[str], select: list[str]) -> list[Item]:
        filters = [] if filters is None else filters
        select = [] if select is None else select
        filters = [f"({filter_.replace('.', '_x002e_')})" for filter_ in filters]
        filters = "and".join(filters)
        select = [f"{field.replace('.', '_x002e_')}" for field in select]
        select = ",".join(select)

        params = {"$filter": filters, "$select": select}
        items = self.get_deferred_items("Items", Item, params)
        return items


