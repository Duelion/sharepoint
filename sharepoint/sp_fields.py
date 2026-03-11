from pydantic import BaseModel, ConfigDict

from .utils import to_camel, replace_key_mapping, COLUMN_ESCAPE


class Field(BaseModel):
    title: str
    field_type_kind: int
    required: bool = True
    type: str = "SP.Field"
    description: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )

    def data(self):
        data = self.model_dump(by_alias=True, exclude={"type"}, exclude_none=True)
        data = replace_key_mapping(data, COLUMN_ESCAPE)
        return data

    def payload(self):
        data = self.data()
        metadata = {"type": self.type}
        return {**data, "__metadata": metadata}

class FieldCreationInformation(Field):
    type: str = "SP.FieldCreationInformation"

    def payload(self):
        payload = super().payload()
        return {"parameters": payload}



class FieldChoices(FieldCreationInformation):
    choices: list[str]
    field_type_kind: int = 6

    def data(self):
        data = super().data()
        data["Choices"] = {"results": self.choices}
        return data


class FieldLookup(FieldCreationInformation):
    lookup_list_id: str
    lookup_field_name: str
    field_type_kind: int = 7


class FieldCalculated(Field):
    formula: str
    type: str = 'SP.FieldCalculated'
    field_type_kind: int = 17
