import datetime
from collections import deque
from collections.abc import Sequence
from enum import Enum
from queue import Queue
from typing import Type, Any, get_origin, get_args

from pydantic import BaseModel, Field, ConfigDict
from pydantic.fields import FieldInfo

from sharepoint import sp_fields

ITERABLE_ORIGINS = (list, set, tuple, frozenset, deque, Sequence)


class Node(BaseModel):
    name: str | None = None
    field: FieldInfo | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
    fields: dict[str, FieldInfo] = Field(default_factory=dict)
    type: Type
    path: list["Node"] = Field(default_factory=list, repr=False)
    is_array: bool = False

    def __init__(self, **data):
        """Incorporar a si mismo dentro del path"""
        path = data.get("path")
        super().__init__(**data)
        if path is not None:
            self.path = path + [self]

    model_config = ConfigDict(arbitrary_types_allowed=True)


def traverse_fields(model: Type[BaseModel]):
    queue: Queue[Node] = Queue()
    root_node = Node(fields=model.model_fields, type=model)
    queue.put(root_node)
    end_nodes = []
    while not queue.empty():
        node = queue.get()
        path = node.path
        for name, field_info in node.fields.items():
            annotation = field_info.annotation
            # Detect if the field is an iterable container (list, set, etc.)
            origin = get_origin(annotation)
            is_array = origin is not None and origin in ITERABLE_ORIGINS
            # Get the inner type for iterables, or the annotation itself
            if is_array:
                args = get_args(annotation)
                type_ = args[0] if args else annotation
            else:
                type_ = annotation

            is_pydantic = isinstance(type_, type) and issubclass(type_, BaseModel)
            fields = type_.model_fields if is_pydantic else {}
            # Extract extra metadata from json_schema_extra
            extra = field_info.json_schema_extra if isinstance(field_info.json_schema_extra, dict) else {}
            sub_node = Node(
                name=name, fields=fields, type=type_, path=path,
                is_array=is_array, field=field_info, extra=extra,
            )
            if is_pydantic:
                queue.put(sub_node)
            else:
                end_nodes.append(sub_node)

    return end_nodes


class SharePointColumn:

    def __init__(self, node: Node):
        self.title = self.reduce_title(node)
        self.type = node.type
        self.required = node.field.is_required()
        self.field_info = node.field
        self.extra = node.extra

    @staticmethod
    def reduce_title(node: Node):
        title = ".".join(node.name for node in node.path)
        return title

    def payload(self):
        extra = dict(self.extra)
        field = extra.pop("sp_field", None)
        if field is None:
            extra["field_type_kind"] = SHAREPOINT_TYPES[self.type]
            field = sp_fields.Field
        # Extract relevant field metadata for the payload
        data = {}
        if self.field_info.description is not None:
            data["description"] = self.field_info.description
        data.update(extra)
        field_instance = field(**data, title=self.title)  # , required=self.required)
        payload = field_instance.payload()
        return payload

    def __repr__(self):
        string = f"{self.title=}, {self.type=}, {self.required=}"
        return string.replace("self.", "")


def pydantic_to_sharepoint(model: Type[BaseModel]):
    nodes = traverse_fields(model)
    columns = [SharePointColumn(node) for node in nodes]
    return columns


SHAREPOINT_TYPES = {'integer': 1,  # 'integer'
                    str: 2,  # 'text'
                    'note': 3,
                    datetime.datetime: 4,  # 'datetime'
                    datetime.date: 4,  # 'datetime'
                    'counter': 5,
                    Enum: 6,
                    'lookup': 7,
                    bool: 8,  # 'boolean'
                    float: 9,  # 'number'
                    int: 9,  # 'number'
                    'currency': 10,
                    'url': 11,
                    'computed': 12,
                    'threading': 13,
                    'guid': 14,
                    'multichoice': 15,
                    'gridchoice': 16,
                    'calculated': 17,
                    'file': 18,
                    'attachments': 19,
                    'user': 20,
                    'recurrence': 21,
                    'crossprojectlink': 22,
                    'modstat': 23,
                    'error': 24,
                    'contenttypeid': 25,
                    'pageseparator': 26,
                    'threadindex': 27,
                    'workflowstatus': 28,
                    'alldayevent': 29,
                    'workfloweventtype': 30,
                    'maxitems': 31}
