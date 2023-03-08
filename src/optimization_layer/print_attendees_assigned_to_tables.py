from typing import Union
import logging

import pandas as pd
import numpy as np

from src.parameters.parameters import Parameters
from src.entity.table import Table
from src.entity.attendee import Attendee

logger: logging.Logger = logging.getLogger(__name__)


def print_tables_compressed(tables: list[Table]):
    tables_to_print = {table: '; '.join(str(attendee) for attendee in table.attendees) for table in tables}
    logger.info("Table\tAttendee")
    for table, attendees_to_print in tables_to_print.items():
        logger.info(f"{str(table)}\t{attendees_to_print}")


def output_solution(parameters: Parameters, tables: list[Table]) -> pd.DataFrame:
    attribute_lists: dict[str, list[str]] = {attribute_name: [] for attribute_name in parameters.attribute_field_names}
    table_id: list[int] = list()
    attendee_id: list[Union[str, int]] = list()
    attendee_name: list[str] = list()
    for table in tables:
        for attendee in table.attendees:
            table_id.append(table.table_id + 1)
            attendee_id.append(attendee.id)
            attendee_name.append(attendee.name)
            for attribute_name in parameters.attribute_field_names:
                attribute_lists[attribute_name].append(attendee.attributes[attribute_name])
    table_assignments_dict_for_pd = {
        "Table": table_id,
        'ID': attendee_id,
        "NAME": attendee_name}
    for attribute_name in parameters.attribute_field_names:
        table_assignments_dict_for_pd[attribute_name] = attribute_lists[attribute_name]

    table_assignments_df = pd.DataFrame(table_assignments_dict_for_pd)
    return table_assignments_df


def output_summary(parameters: Parameters, tables: list[Table]) -> pd.DataFrame:
    attendee_solution_df = output_solution(parameters, tables)
    # attendee_solution_df.set_index('Table')
    table_scores_df = pd.DataFrame({"Table": [table.table_id + 1 for table in tables],
                                    "Score": [table.score() for table in tables],
                                    "Penalty": [table.upper_bound_violations() for table in tables],
                                    "Table_Size": [len(table.attendees) for table in tables]})
    table_scores_df.set_index('Table', inplace=True)

    upper_bound_df = Table.build_upper_bound_df()
    print(upper_bound_df.transpose())

    summary_df = table_scores_df
    for attribute_name in parameters.attribute_field_names:
        summary_df = summary_df.join(attendee_solution_df.pivot_table(index="Table",
                                                                      values=parameters.id_field_name,
                                                                      columns=attribute_name,
                                                                      fill_value=0,
                                                                      aggfunc=np.count_nonzero))

    return summary_df
