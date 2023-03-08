from typing import Union
import logging

import pandas as pd

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

    _, group_scores = total_scores(groups, diversity_score)

    attribute_by_group_count = ubba.attribute_counts_by_group(num_groups, groups, attendees)
    _, penalty_scores = ubba.total_upper_bound_penalty(attribute_by_group_count)

    group_scores_df = pd.DataFrame({"Group": [table.table_id + 1 for table in tables],
                                    "Score": [table.score() for table in tables],
                                    "Penalty": [0.0 for table in tables],
                                    "Table_Size": [len(table.attendees) for table in tables]})
    group_scores_df.set_index('Group')
    summary_df = (
        group_scores_df
        .join(attendee_solution_df.pivot_table(index="Group", values='Gender', columns="Role", fill_value=0,
                                               aggfunc=np.count_nonzero))
        .join(attendee_solution_df.pivot_table(index="Group", values='Gender', columns="Office", fill_value=0,
                                               aggfunc=np.count_nonzero))
        .join(attendee_solution_df.pivot_table(index="Group", values='Gender', columns="Start_Year", fill_value=0,
                                               aggfunc=np.count_nonzero))
        .join(attendee_solution_df.pivot_table(index="Group", values='Office', columns="Gender", fill_value=0,
                                               aggfunc=np.count_nonzero))
    )
    summary_df['Group'] = summary_df['Group'] + 1
    return summary_df
