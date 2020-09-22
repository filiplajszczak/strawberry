import dataclasses
from dataclasses import dataclass
from typing import List, Optional, Type, cast

from pydantic import BaseModel
from pydantic.fields import ModelField
from strawberry.type import _process_type
from strawberry.types.types import FederationTypeParams, FieldDefinition


class UnregisteredTypeException(Exception):
    def __init__(self, type: BaseModel):
        message = (
            f"Cannot find a Strawberry Type for {type} did you forget to register it?"
        )

        super().__init__(message)


def resolve_type(field: ModelField) -> Type:
    field_type = {str: str, int: int}.get(field.type_)

    if field_type is None:
        if issubclass(field.type_, BaseModel):
            if hasattr(field.type_, "_strawberry_type"):
                return field.type_._strawberry_type

            raise UnregisteredTypeException(field.type_)

    return cast(Type, field_type)


def type(
    model: Type[BaseModel],
    *,
    name: str = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str = None,
    federation: Optional[FederationTypeParams] = None,
):
    def wrap(cls):

        fields = model.__fields__

        print(fields)
        print(model.__annotations__)

        base_fields: List[FieldDefinition] = []

        for field_name, field in fields.items():
            base_fields.append(
                FieldDefinition(
                    name=field_name,
                    origin_name=field_name,
                    origin=field,
                    type=resolve_type(field),
                    is_optional=not field.required,
                )
            )

        # print(base_fields)

        cls = dataclasses.make_dataclass(
            cls.__name__, [(field.name, field.type) for field in base_fields]
        )

        _process_type(
            cls,
            name=name,
            is_input=is_input,
            is_interface=is_interface,
            description=description,
            federation=federation,
            # _base_fields=base_fields,
        )

        model._strawberry_type = cls
        model._type_definition = cls._type_definition

        def from_pydantic(instance: model, **kwargs) -> model:
            instance_kwargs = instance.dict()

            # TODO: convert nested data

            return model(**{**instance_kwargs, **kwargs})

        model.from_pydantic = staticmethod(from_pydantic)

        return cls

    return wrap
