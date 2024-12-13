import json
import pathlib
from enum import Enum

import pytest
from pydantic.v1 import BaseSettings, BaseModel, Field

from sharepoint import SharePoint, SharepointSession, sp_fields

"""
PyTest permite crear "fixtures" para obejetos/ parametros resuables en los distintos tests.
"""


@pytest.fixture(scope='session')
def settings():
    class PyTestSettings(BaseSettings):
        client_id: str
        tenant_id: str
        secret: str
        domain: str
        site: str
        delay_secs: int = 0.1
        num_retries: int = 5

        class Config:
            env_prefix = "TEST_"

    return PyTestSettings()

@pytest.fixture(scope='session')
def sharepoint_session(settings):
    session = SharepointSession(delay_secs=settings.delay_secs, num_retries=settings.num_retries)
    return session


@pytest.fixture(scope='session')
def sharepoint(settings, sharepoint_session):
    sharepoint = SharePoint(client_id=settings.client_id, tenant_id=settings.tenant_id, secret=settings.secret,
                            domain=settings.domain, site=settings.site, session=sharepoint_session)
    return sharepoint




@pytest.fixture(scope='function')
def expected_data(request):
    func_name = request.node.originalname
    directory = pathlib.Path(__file__).parent / "expected"
    file_path = f"{directory}/{func_name}.json"
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        with open(file_path, 'w') as file:
            json.dump({}, file)
            raise FileNotFoundError(f"Archivo {file_path} no encontrado, por lo que ha sido creado")


@pytest.fixture(scope='session')
def pydantic_model():
    class Color(Enum):
        blue = "Blue"
        red = "Red"


    class County(BaseModel):
        name: str  = Field(...)
        population: int
        color: Color = Field(..., sp_field=sp_fields.FieldChoices, choices=[item.value for item in Color])

    class Info(BaseModel):
        governor: str
        age: int

    class State(BaseModel):
        state: str = Field(..., description="Testing")
        shortname: str
        info: Info
        counties: list[County]

    return State


@pytest.fixture(scope='session')
def pydantic_parsed_data(pydantic_model):
    data = [
        {
            "state": "Florida",
            "shortname": "FL",
            "info": {"governor": "Rick Scott", "age": 45},
            "counties": [
                {"name": "Dade", "population": 12345},
                {"name": "Broward", "population": 40000},
                {"name": "Palm Beach", "population": 60000},
            ],
        },
        {
            "state": "Ohio",
            "shortname": "OH",
            "info": {"governor": "John Kasich", "age": 60},
            "counties": [
                {"name": "Summit", "population": 1234},
                {"name": "Cuyahoga", "population": 1337},
            ],
        },
    ]
    parsed = [pydantic_model(**entry) for entry in data]
    return parsed
