from pathlib import Path
import datetime
import logging
import argparse
import signal

import pandas as pd

from src.parameters.parameters import Parameters
from src.data_layer.read_attendees import read_attendees
from src.optimization_layer.initialize_tables import initialize_tables
from src.optimization_layer.develop_initial_solution import initial_solution
from src.optimization_layer.print_attendees_assigned_to_tables import output_solution

logger: logging.Logger = logging.getLogger()   # set in main()
stop_executing: bool = False


def setup_logger(output_dir: str):
    global logger

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(output_dir, mode='w')
    fh.setLevel(logging.INFO)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    fh_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")
    ch_formatter = logging.Formatter('%(levelname)s: %(message)s')
    fh.setFormatter(fh_formatter)
    ch.setFormatter(ch_formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def ctrl_c_handler(_signum, _frame):
    """When ctrl-c is pressed, wait till next re-optimization occurs and write out best answer then exit"""
    global stop_executing
    stop_executing = True
    logger.info("Control-C was pressed.  Will stop optimizing and output best solution so far")


def main():
    global logger

    parser = argparse.ArgumentParser()
    default_config_loc = r'C:\DocumentsOliverWyman\CCG_Grouping_Model\maximum_diversity\data_and_log_files\config.yml'
    parser.add_argument("--config_location", type=str, help="YAML configuration file location - full file path",
                        default=default_config_loc)
    args = parser.parse_args()
    start_time = datetime.datetime.now()

    signal.signal(signal.SIGINT, ctrl_c_handler)

    path_to_config_file = Path(args.config_location)
    parameters = Parameters(path_to_config_file)
    path_to_data_and_log_files = Path(parameters.data_directory)
    log_file_name = str(path_to_data_and_log_files.parent.absolute() / parameters.log_file_name)
    logger = setup_logger(log_file_name)

    logger.info(f'Parameters:\n{parameters.display()}')

    attendees = read_attendees(parameters)
    tables = initialize_tables(parameters, attendees)
    print(attendees)
    print(tables)

    pd.options.display.max_rows=None
    pd.options.display.max_columns = None
    pd.options.display.width = None
    initial_solution(tables, attendees, parameters)

    print(output_solution(parameters, tables))

if __name__ == '__main__':
    main()
