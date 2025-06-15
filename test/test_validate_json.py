import json
import pathlib

import jsonschema

from pytest import raises

from jsonvalidator.validate_json import process_command_line, main, InvalidJSON


def write_files(tmp_path, data, schema=None):
    data_path = tmp_path / "data.json"
    data_path.write_text(data_to_string(data), encoding="utf-8")
    if schema:
        schema_path = tmp_path / "schema.json"
        schema_path.write_text(data_to_string(schema), encoding="utf-8")
        return str(data_path), str(schema_path)

    else:
        return str(data_path)


def data_to_string(data):
    if isinstance(data, str):
        return data
    else:
        return json.dumps(data, indent=4)


def test_command_line_accepts_data_path():
    args = ["testing", "--data-path", "/some/path/to/json/data.json"]
    runtime_config = process_command_line(args)
    assert isinstance(runtime_config.data_path, pathlib.Path)
    assert runtime_config.schema_path is None


def test_command_line_accepts_schema_path():
    args = [
        "testing",
        "--data-path",
        "/some/path/to/json/data.json",
        "--schema-path",
        "/some/path/to/json/schema.json",
    ]
    runtime_config = process_command_line(args)
    assert isinstance(runtime_config.data_path, pathlib.Path)
    assert isinstance(runtime_config.schema_path, pathlib.Path)


def test_command_line_accepts_abbreviated_names():
    args = [
        "testing",
        "--data",
        "/some/path/to/json/data.json",
        "--schema",
        "/some/path/to/json/schema.json",
    ]
    runtime_config = process_command_line(args)
    assert isinstance(runtime_config.data_path, pathlib.Path)
    assert isinstance(runtime_config.schema_path, pathlib.Path)


def test_command_line_requires_data_path():
    args = ["testing"]
    with raises(SystemExit):
        process_command_line(args)


def test_command_line_prints_help_with_long_flag():
    args = ["testing", "--help"]
    with raises(SystemExit):
        process_command_line(args)


def test_command_line_print_help_with_short_flag():
    args = ["testing", "-h"]
    with raises(SystemExit):
        process_command_line(args)


def test_main_returns_zero_for_valid_json(tmp_path):
    data_path = write_files(tmp_path, data=VALID_JSON)
    args = ["testing", "--data-path", data_path]
    return_code = main(args)
    assert return_code == 0


def test_main_returns_zero_for_data_satisfying_schema(tmp_path):
    data_path, schema_path = write_files(
        tmp_path,
        data=SATISFIES_SCHEMA,
        schema=VALID_SCHEMA,
    )
    args = ["testing", "--data-path", data_path, "--schema-path", schema_path]
    return_code = main(args)
    assert return_code == 0


def test_main_fails_when_data_content_is_invalid_json(tmp_path):
    data_path = write_files(tmp_path, data=INVALID_JSON)
    args = ["testing", "--data-path", data_path]
    with raises(InvalidJSON):
        main(args)


def test_main_fails_when_schema_content_is_invalid_json(tmp_path):
    data_path, schema_path = write_files(tmp_path, data=VALID_JSON, schema=INVALID_JSON)
    args = ["testing", "--data-path", data_path, "--schema-path", schema_path]
    with raises(InvalidJSON):
        main(args)


def test_main_fails_when_data_does_not_satisfy_schema(tmp_path):
    data_path, schema_path = write_files(
        tmp_path,
        data=VALID_JSON,
        schema=VALID_SCHEMA,
    )
    args = ["testing", "--data-path", data_path, "--schema-path", schema_path]
    with raises(jsonschema.exceptions.ValidationError):
        main(args)


INVALID_JSON = """
{
  "a" : 1,
   2
}
"""

VALID_JSON = {
    "a": 1,
}

INVALID_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "x": "number",  # <- That is the invalid part. It should be {"type" : "number"}
        "y": "number",
    },
}

VALID_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "x": {"type": "number"},
        "y": {"type": "number"},
    },
    "required": ["x", "y"],
    "additionalProperties": False,
}

SATISFIES_SCHEMA = {
    "x": 3.0,
    "y": 4.0,
}
