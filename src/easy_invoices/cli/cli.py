"""cli functions"""

from enum import Enum
from dataclasses import asdict
from typing import Any, Dict, List, Type
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
data_classes: dict[DataTypes, Type[Data.SerializableData]] = {
    DataTypes.Company: Data.Company,
    DataTypes.Contact: Data.Contact,
    DataTypes.Options: Data.Options,
    DataTypes.Preset: Data.Preset,
}


def get_datatype_from_string(string: str) -> DataTypes:
    """returns the enum that corresponds to the string"""
    for item in DataTypes:
        if item.value == string.lower():
            return item
    raise ValueError(f"No DataType found with value '{string}'")


@cli.command()
def show_all(data_type: DataTypes) -> None:
    """prints the list of saved data files of the given type"""
    typer.echo(data_classes[data_type]().list())


@cli.command()
def show(data_type: DataTypes, name: str) -> None:
    typer.echo(data_classes[data_type](id=name).load())


@cli.command()
def new(data_type: DataTypes, id_field: str = "") -> str:
    """prompts for creation of a new data file of the specified type.
    returns the id of the newly created file"""
    # instantiate the class
    selected_class = data_classes[data_type]()
    if id_field != "":
        selected_class.id = id_field
    populated_fields: dict[str, Any] = {}
    if data_type == DataTypes.Preset:
        selected_class = Data.Preset()
        populated_fields = _preset_dict_from_prompt(selected_class)
    else:
        populated_fields = _dict_from_prompt(selected_class.asdict)

    # make a new instance using the given values, and save to json
    instance: Data.SerializableData = selected_class.__class__(
        **populated_fields
    )

    if instance.save():
        typer.echo(f"new {data_type.value} created: '{instance.id}'")
        return instance.id

    if typer.confirm(
        f"{data_type.value} '{instance.id}' already exisits. would you like to overwrite it?"
    ):
        instance.save(True)
        typer.echo(f"updated {data_type.value} '{instance.id}'")

    return instance.id


# === private functions ===


def _dict_from_prompt(
    dictionary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Prompts the user to populate fields on a SerializableData instance.
    Works recursively for nested classes and lists.
    """
    for key, value in dictionary.items():
        if isinstance(value, dict):
            dict_value: dict[str, Any] = value
            dictionary[key] = _dict_from_prompt(dict_value)
        elif isinstance(value, list):
            list_value: list[Any] = value
            num_items: int = typer.prompt(
                f"How many '{key}' would you like to define?",
                default=0,
                type=int,
            )
            dictionary[key] = _list_from_prompt([list_value[0]] * num_items)
        else:
            value: Any = value
            dictionary[key] = typer.prompt(
                key,
                default=value,
                show_default=bool(value),
            )
    return dictionary


def _list_from_prompt(input_list: list[Any]) -> List[Any]:
    """prompt for nested values in a list"""
    for i, item in enumerate(input_list):
        if isinstance(item, dict):
            dict_item: dict[str, Any] = item
            input_list[i] = _dict_from_prompt(dict_item)
        elif isinstance(item, list):
            list_item: list[Any] = item
            input_list[i] = _list_from_prompt(list_item)
        else:
            input_list[i] = typer.prompt(
                f"Item {i+1}", default=item, show_default=bool(item)
            )
    return input_list


def _preset_dict_from_prompt(preset: Data.Preset) -> Dict[str, str]:
    """prompt for filling out a preset.
    checks that the specififed company, contact, options etc exist,
    and if not asks if the user would like to create them
    """
    values: Dict[str, str] = asdict(preset)
    for field in values.keys():
        values[field] = _prompt_for_preset_field(preset, field, values[field])
    return values


def _prompt_for_preset_field(
    preset: Data.Preset, field: str, value: str
) -> str:
    """returns the id of the specified data file, or the new one created"""
    value = typer.prompt(field, default=value, show_default=bool(value))
    if field == "id":
        return value

    # create a class instance with the specified id, and check if it exisits as a file
    temp_class = data_classes[get_datatype_from_string(field)](id=value)
    if temp_class.exists:
        return value

    if typer.confirm(
        f"no {field} with id '{value}' found. would you like to create it?",
        True,
    ):
        # create a new data file
        return new(get_datatype_from_string(field), value)

    # ask again
    _prompt_for_preset_field(preset, field, value)
    return value


if __name__ == "__main__":
    cli()
