#!/usr/bin/env python

import libconf
import argparse
import os
import re
import sys
from typing import Dict, Any
from dotenv import dotenv_values

VALID_OGN_ENV_PREFIXES = ("ADSB_", "APRS_", "Beacon_", "DDB_", "Demodulator_", "HTTP_", "Position_", "RF_")

def unflatten_dict(d: Dict[str, str]) -> Dict[str, Any]:
    """Unflattens a dictionary with flattened keys."""

    unflattened_dict = {}
    for key, value in d.items():
        parts = key.split('_')
        d = unflattened_dict
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value
    return unflattened_dict

def flatten_dict(d: Dict[str, Any], parent_key: str ='') -> Dict[str, str]:
    """Flattens a nested dictionary."""

    items = []
    for k, v in d.items():
        new_key = f"{parent_key}_{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)

def is_numeric(value):
    if isinstance(value, (int, float)):
        return True
    elif isinstance(value, str):
        return bool(re.match(r'^-?\d+(\.\d+)?$', value))
    else:
        return False

def validate_mandatory_parameters(parameters: Dict[str, Any]) -> None:
    """Check if mandatory parameter APRS_Call, and Position_xxx are correctly set."""

    aprs_call_regex = re.compile(r"^[A-Za-z][A-Za-z0-9]{2,7}$")
    try:
        if "APRS_Call" not in parameters or not parameters['APRS_Call']:
            raise ValueError("Setting 'APRS_Call' missing or empty.")
        elif not aprs_call_regex.match(parameters["APRS_Call"]):
            raise ValueError(f"Invalid APRS_Call: {parameters['APRS_Call']}")

        elif "Position_Latitude" not in parameters or not parameters['Position_Latitude']:
            raise ValueError("Setting 'Position_Latitude' missing or empty.")
        elif not is_numeric(parameters["Position_Latitude"]):
            raise ValueError(f"Invalid Position_Latitude: {parameters['Position_Latitude']}")
        elif not -90 < float(parameters["Position_Latitude"]) < 90:
            raise ValueError(f"Position_Latitude not in range (-90..+90)")

        elif "Position_Longitude" not in parameters or not parameters['Position_Longitude']:
            raise ValueError("Setting 'Position_Longitude' missing or empty.")
        elif not is_numeric(parameters["Position_Longitude"]):
            raise ValueError(f"Invalid Position_Longitude: {parameters['Position_Longitude']}")
        elif not -180 < float(parameters["Position_Longitude"]) < 180:
            raise ValueError(f"Position_Longitude not in range (-180..+180)")

        elif "Position_Altitude" not in parameters or not parameters['Position_Altitude']:
            raise ValueError(f"Setting 'Position_altitude' missing or empts.")
        elif not is_numeric(parameters["Position_Altitude"]):
            raise ValueError(f"Invalid Position_Altitude: {parameters['Position_Altitude']}")
        elif not 0 < float(parameters["Position_Altitude"]) < 8848:
            raise ValueError(f"Position_Altitude not in range (0..8848)")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert OGN receiver configuration between libconfig format and environment parameters')
    parser.add_argument('--file', type=str, help="configuration file (.env or .conf)", required=False, default='')

    args = parser.parse_args()

    if args.file:
        file_path = os.path.abspath(args.file)
        if not os.path.exists(file_path):
            print(f"Error: file '{args.file}' does not exist")
            sys.exit(1)

        # Read parameters from .env file and print out like .conf
        if args.file.endswith('.env'):
            parameters = {k: v for k, v in dotenv_values('.env').items() if k.startswith((VALID_OGN_ENV_PREFIXES))}
            validate_mandatory_parameters(parameters)
            config = unflatten_dict(parameters)
            print(libconf.dumps(config))

        # Read parameters from .conf file and print out like .env
        elif args.file.endswith('.conf'):
            with open(file_path, 'r') as f:
                config = libconf.load(f)
            parameters = flatten_dict(config)
            validate_mandatory_parameters(parameters)
            print('\n'.join(f"{k}={v}" for k,v in parameters.items()))

        else:
            print(f"Error: Unknown file format: '{args.file}'", file=sys.stderr)
            sys.exit(1)

    else:
        # Read parameters from current environment and print out like .conf
        parameters = {k: v for k, v in os.environ.items() if k.startswith((VALID_OGN_ENV_PREFIXES))}
        validate_mandatory_parameters(parameters)
        config = unflatten_dict(parameters)
        print(libconf.dumps(config))
