"""cli functions"""

from enum import Enum
from dataclasses import fields, is_dataclass
from typing import Any, Dict, get_args, get_origin
import typer
import easy_invoices.data as Data


cli: typer.Typer = typer.Typer()


class DataTypes(Enum):
    Company = "company"
    Contact = "contact"
    Options = "options"
    Preset = "preset"


# maps data types to the correspoinding data class
data_classes = {
    DataTypes.Company: Data.Company,
    DataTypes.Contact: Data.Contact,
    DataTypes.Options: Data.Options,
    DataTypes.Preset: Data.Preset,
}


def get_datatype_from_string(string: str) -> DataTypes:
    for item in DataTypes:
        if item.value == string:
            return item
    raise ValueError(f"No DataType found with value '{string}'")


def recursive_prompt_for_fields(obj: Any) -> Dict[str, Any]:
    """
    Prompts the user to populate fields on a dataclass. Works recursively for nested classes.
    """
    values: Dict[str, Any] = {}

    for field in fields(obj):
        field_value = getattr(obj, field.name)
        field_type = field.type
        origin = get_origin(field_type)

        if origin is list:
            item_type = get_args(field_type)[0]  # Get the type of list items

            num_items = int(
                typer.prompt(
                    f"How many '{field.name}' would you like to define?",
                    default=len(field_value) if field_value else 0,
                    show_default=True,
                )
            )

            values[field.name] = []
            for i in range(num_items):
                if is_dataclass(item_type):
                    item_instance = item_type()
                    item_data = recursive_prompt_for_fields(item_instance)
                    values[field.name].append(item_type(**item_data))
                else:
                    item_value = typer.prompt(
                        f"Item {i+1} of field '{field.name}' ({item_type.__name__})",
                        show_default=False,
                    )
                    values[field.name].append(item_type(item_value))
        elif is_dataclass(field_value):
            nested_values = recursive_prompt_for_fields(field_value)
            values[field.name] = field_value.__class__(**nested_values)
        else:
            values[field.name] = typer.prompt(
                f"{field.name}",
                default=field_value,
                show_default=False,
                type=field_type,
            )

    return values


def prompt_for_preset(preset: Data.SerializableData) -> Dict[str, Any]:
    values: Dict[str, str] = {}
    for field in fields(preset):
        values[field.name] = prompt_for_preset_field(preset, field.name)
    return values


def prompt_for_preset_field(preset: Data.SerializableData, field: str) -> str:
    field_value = getattr(preset, field)
    value = typer.prompt(field, default=field_value, show_default=False)
    if field == "id":
        return value
    temp_class = data_classes[get_datatype_from_string(field)]()
    temp_class.id = value
    if not temp_class.exists:
        if typer.confirm(
            f"no {field} with id '{value}' found. would you like to create it?"
        ):
            value = new(get_datatype_from_string(field))
        else:
            prompt_for_preset_field(preset, field)
    return value


@cli.command()
def show_all(data_type: DataTypes):
    selected_class = data_classes[data_type]()
    typer.echo(selected_class.list())


@cli.command()
def new(data_type: DataTypes) -> str:
    # instantiate the class
    selected_class = data_classes[data_type]()

    if data_type == DataTypes.Preset:
        filled_fields = prompt_for_preset(selected_class)
    else:
        filled_fields = recursive_prompt_for_fields(selected_class)
    # make a new instance using the given values, and save to json
    instance = selected_class.__class__(**filled_fields)
    if not instance.save():
        if not typer.confirm(
            f"{data_type.value} '{instance.id}' already exisits. would you like to overwrite it?"
        ):
            return instance.id
        instance.save(True)
    typer.echo(f"new {data_type.value} created: '{instance.id}'")
    return instance.id


if __name__ == "__main__":
    cli()
