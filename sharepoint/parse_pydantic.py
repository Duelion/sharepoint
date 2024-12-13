import datetime
from enum import Enum
from queue import Queue
from typing import Type, Any

from pydantic import BaseModel, Field
from pydantic.v1.fields import ModelField
from pydantic.v1.fields import SHAPE_LIST, SHAPE_TUPLE_ELLIPSIS, SHAPE_SEQUENCE, SHAPE_SET, SHAPE_FROZENSET, \
    SHAPE_ITERABLE, SHAPE_DEQUE

from sharepoint import sp_fields

PYDANTIC_ITERABLE = {SHAPE_LIST, SHAPE_TUPLE_ELLIPSIS, SHAPE_SEQUENCE, SHAPE_SET, SHAPE_FROZENSET, SHAPE_ITERABLE,
                     SHAPE_DEQUE}


class Node(BaseModel):
    name: str = None
    field: ModelField = None
    extra: dict[str, Any] = Field(default_factory=dict)
    fields: dict[str, ModelField] = Field(default_factory=dict)
    type: Type
    path: list["Node"] = Field(default_factory=list, repr=False)
    is_array: bool = False

    def __init__(self, **data):
        """Incorporar a si mismo dentro del path"""
        path = data.get("path")
        super().__init__(**data)
        if path is not None:
            self.path = path + [self]

    class Config:
        arbitrary_types_allowed = True


def traverse_fields(model: Type[BaseModel]):
    queue: Queue[Node] = Queue()
    root_node = Node(fields=model.__fields__, type=model)
    queue.put(root_node)
    end_nodes = []
    while not queue.empty():
        node = queue.get()
        path = node.path
        for name, field in node.fields.items():
            is_array = field.shape in PYDANTIC_ITERABLE
            type_ = field.type_
            is_pydantic = issubclass(type_, BaseModel)
            fields = type_.__fields__ if is_pydantic else {}
            sub_node = Node(name=name, fields=fields, type=type_, path=path, is_array=is_array, field=field,
                            extra=field.field_info.extra)
            if is_pydantic:
                queue.put(sub_node)
            else:
                end_nodes.append(sub_node)

    return end_nodes


class SharePointColumn:

    def __init__(self, node: Node):
        self.title = self.reduce_title(node)
        self.type = node.type
        self.required = node.field.required
        self.field_info = node.field.field_info
        self.extra = node.extra

    @staticmethod
    def reduce_title(node: Node):
        title = ".".join(node.name for node in node.path)
        return title

    def payload(self):
        try:
            field = self.extra.pop("sp_field")
        except KeyError:
            self.extra["field_type_kind"] = SHAREPOINT_TYPES[self.type]
            field = sp_fields.Field
        data = dict(self.field_info.__repr_args__())
        data.pop("extra")  # Eliminar elemento default de __repr_args__
        data.update(self.extra)
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
