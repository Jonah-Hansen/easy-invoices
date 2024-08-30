"""cli functions"""

from enum import Enum
from dataclasses import Field, fields, is_dataclass
from typing import Any, Dict, List, get_args, get_origin
import typer
import easy_invoices.data as Data


# initialize typer cli
cli: typer.Typer = typer.Typer()


# possible args for crud operations
class DataTypes(Enum):
    Company = "company"
    Contact = "contact"
    Options = "options"
    Preset = "preset"


# maps data types to the correspoinding data class
data_classes: dict[DataTypes, Data.SerializableData] = {
    DataTypes.Company: Data.Company,
    DataTypes.Contact: Data.Contact,
    DataTypes.Options: Data.Options,
    DataTypes.Preset: Data.Preset,
}


def get_datatype_from_string(string: str) -> DataTypes:
    """returns the enum that corresponds to the string"""
    for item in DataTypes:
        if item.value == string:
            return item
    raise ValueError(f"No DataType found with value '{string}'")


def prompt_for_list(field: Field[List[Any]], value: List[Any]) -> List[Any]:
    """prompt for nested values in a list"""
    values: List[Any] = []
    item_type = get_args(field.type)[0]  # Get the type of list items
    num_items: int = typer.prompt(
        f"How many '{field.name}' would you like to define?",
        default=len(value) if value else 0,
        show_default=False,
        type=int,
    )
    for i in range(num_items):
        if is_dataclass(item_type):
            item_data = recursive_prompt_for_fields(item_type())
            values.append(item_type(**item_data))
        else:
            item_value = typer.prompt(
                f"Item {i+1} of '{field.name}'",
                show_default=False,
            )
            values.append(item_type(item_value))
    return values


def recursive_prompt_for_fields(
    instance: Data.SerializableData,
) -> Dict[str, Any]:
    """
    Prompts the user to populate fields on a dataclass. Works recursively for nested classes.
    """
    values: Dict[str, Any] = {}

    for field in fields(instance):
        field_value = getattr(instance, field.name)

        if get_origin(field.type) is list:
            # field is list
            values[field.name] = prompt_for_list(field, field_value)
        elif is_dataclass(field_value):
            # field is nested dataclass
            nested_values = recursive_prompt_for_fields(field_value)
            values[field.name] = field_value.__class__(**nested_values)
        else:
            # filed is a basic type
            values[field.name] = typer.prompt(
                field.name,
                default=field_value,
                show_default=False,
                type=field.type,
            )
    return values


def prompt_for_preset(preset: Data.SerializableData) -> Dict[str, Any]:
    """prompt for filling out a preset.
    checks that the specififed company, contact, options etc exist,
    and if not asks if the user would like to create them
    """
    values: Dict[str, str] = {}
    for field in fields(preset):
        values[field.name] = prompt_for_preset_field(preset, field.name)
    return values


def prompt_for_preset_field(preset: Data.SerializableData, field: str) -> str:
    """returns the id of the specified data file, or the new one created"""
    field_value = getattr(preset, field)
    value = typer.prompt(field, default=field_value, show_default=False)
    if field == "id":
        return value
    # create a class instance with the specified id, and check if it exisits as a file
    temp_class = data_classes[get_datatype_from_string(field)](id=value)
    if not temp_class.exists:
        if typer.confirm(
            f"no {field} with id '{value}' found. would you like to create it?"
        ):
            # create a new data file
            value = new(get_datatype_from_string(field))
        else:
            # ask again
            prompt_for_preset_field(preset, field)
    return value


@cli.command()
def show_all(data_type: DataTypes):
    """prints the list of saved data files of the given type"""
    selected_class: Data.SerializableData = data_classes[data_type]()
    typer.echo(selected_class.list())


@cli.command()
def show(data_type: DataTypes, name: str):
    selected_class: Data.SerializableData = data_classes[data_type](id=name)
    selected_class.load()
    typer.echo(selected_class)


@cli.command()
def new(data_type: DataTypes) -> str:
    """prompts for creation of a new data file of the specified type.
    returns the id of the newly created file"""
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
