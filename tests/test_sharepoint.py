import pytest
from pydantic import BaseModel

from sharepoint.parse_pydantic import pydantic_to_sharepoint

def test_get_folder(sharepoint):
    sharepoint.get_folder("Shared Documents/PreviRed")

def test_create_list(sharepoint):
    sharepoint.create_list("TestingList", "hahaha desc")

def test_delete_list(sharepoint):
    sp_list = sharepoint.get_list("TestingList")
    sp_list.delete()

def test_get_all_lists(sharepoint):
    sp_lists = sharepoint.get_all_lists()
    print(sp_lists)

def test_get_list_by_title(sharepoint):
    sharepoint.get_list("TestingList")

def test_create_item_list(sharepoint):
    sharepoint.create_item_list("TestingList")

def test_modelos(pydantic_model, sharepoint):
    sp_list = sharepoint.get_list("TestingList")
    fields = pydantic_to_sharepoint(pydantic_model)
    for field in fields:
        data = field.payload()
        sp_list.create_field(data)