import os
import sys
from pathlib import Path
import datetime
import logging
import argparse
import signal

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from src.parameters.parameters import Parameters
from src.data_layer.read_attendees import read_attendees
from src.optimization_layer.initialize_tables import initialize_tables
from src.optimization_layer.develop_initial_solution import initial_solution
from src.optimization_layer.print_attendees_assigned_to_tables import output_solution, output_summary
from src.optimization_layer.reoptimize import iterate_reoptimization
import src.globals as globals

logger: logging.Logger = logging.getLogger()   # set in main()


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
    globals.stop_execution = True
    logger.info("Control-C was pressed.  Will stop optimizing and output best solution so far")


def main():
    global logger

    parser = argparse.ArgumentParser()
    default_config_loc = r'C:\DocumentsOliverWyman\Table_Arrangements_Optimization\data_and_log_files\config.yml'
    parser.add_argument("--config_location", type=str, help="YAML configuration file location - full file path",
                        default=default_config_loc)
    args = parser.parse_args()

    signal.signal(signal.SIGINT, ctrl_c_handler)

    path_to_config_file = Path(args.config_location)
    parameters = Parameters(path_to_config_file)
    log_file_name = str(parameters.data_directory / parameters.log_file_name)
    logger = setup_logger(log_file_name)

    logger.info(f'Parameters:\n{parameters.display()}')

    attendees = read_attendees(parameters)
    tables = initialize_tables(parameters, attendees)
    logger.info(f'Attendees: {attendees}')

    pd.options.display.max_rows=None
    pd.options.display.max_columns = None
    pd.options.display.width = None
    initial_solution(tables, attendees, parameters)

    logger.info(f'Initial Solution\n{output_solution(parameters, tables)}')

    logger.info(f'Table summary statistics for initial solution\n{output_summary(parameters, tables)}')

    iterate_reoptimization(parameters, tables)

    solution_df = output_solution(parameters, tables)
    summary_df = output_summary(parameters, tables)

    solution_df.to_csv(parameters.data_directory / parameters.table_assignments_file_name, index=False)
    summary_df.to_csv(parameters.data_directory / parameters.table_summary_statistics, index=True)
    logger.info(f'Finished in {(datetime.datetime.now() - globals.start_time).total_seconds():.2f} seconds')

if __name__ == '__main__':
    main()
