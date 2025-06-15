"""
Validate JSON data files
"""

import json
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Protocol, Optional, Any

import jsonschema


class RuntimeConfig(Protocol):
    @property
    def data_path(self) -> Path:
        pass

    @property
    def schema_path(self) -> Optional[Path]:
        pass


class InvalidJSON(RuntimeError):
    """
    An error indicating that the content a file is not valid JSON
    """


class SchemaNotSatisfied(RuntimeError):
    """
    An error indicating that the schema was not satisfied by the data
    """


def run_app() -> None:
    """
    Execute the JSON validation application
    """
    try:
        sys.exit(main(sys.argv))
    except jsonschema.exceptions.ValidationError as error:
        print(error, file=sys.stderr, flush=True)
        sys.exit(1)
    except RuntimeError as error:
        print(error, file=sys.stderr, flush=True)
        sys.exit(2)


def main(args) -> int:
    """
    Run the validation
    """
    runtime_config = process_command_line(args)
    run(runtime_config)
    return 0


def process_command_line(args: list[str]) -> RuntimeConfig:
    """
    Return a runtime configuration object based on
    the command line arguments
    """
    parser = make_command_line_parser(args[0])
    runtime_config = parser.parse_args(args[1:])
    return runtime_config


def make_command_line_parser(prog: str) -> ArgumentParser:
    """
    Return a parser for the command line
    """

    parser = ArgumentParser(prog=prog)

    parser.add_argument(
        "--data-path",
        type=Path,
        required=True,
        metavar="DATA",
        help="Path to the JSON data file",
    )

    parser.add_argument(
        "--schema-path",
        type=Path,
        required=False,
        metavar="SCHEMA",
        help="Optional path to the JSON schema file",
    )

    return parser


def run(runtime_config: RuntimeConfig) -> None:
    """
    Validate the JSON data
    """
    if runtime_config.schema_path:
        validate_with_schema(runtime_config)
    else:
        validate_json(runtime_config)


def validate_with_schema(runtime_config: RuntimeConfig) -> None:
    """
    Validate the JSON data against a JSON schema
    """
    data = load_json(runtime_config.data_path)
    schema = load_json(extract_path(runtime_config.schema_path))
    jsonschema.validate(data, schema)


def extract_path(path: Optional[Path]) -> Path:
    """
    Return the path from an optional path value
    """
    if isinstance(path, Path):
        return path
    else:
        raise RuntimeError("Expected a path")


def validate_json(runtime_config: RuntimeConfig) -> None:
    """
    Validate the JSON data is valid JSON
    """
    load_json(runtime_config.data_path)


def load_json(path: Path) -> Any:
    """
    Load and return JSON data from the input path
    """
    try:
        with open(path, "r", encoding="utf-8") as inp:
            data = json.load(inp)
    except json.decoder.JSONDecodeError as error:
        raise make_error(path, error)
    return data


def make_error(path: Path, error: json.decoder.JSONDecodeError) -> InvalidJSON:
    """
    Return an error that is formatted for IDE linking to source
    """
    raise InvalidJSON(
        ERROR_STRING.format(
            path=path.resolve(),
            line=error.lineno,
            column=error.colno,
            message=error.msg,
        )
    )


ERROR_STRING = """{path}:{line}:{column}: Error
  {message}"""


if __name__ == "__main__":
    run_app()
