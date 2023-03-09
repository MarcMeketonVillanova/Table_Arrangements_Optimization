from collections import defaultdict
import logging

from src.parameters.parameters import Parameters
from src.entity.attendee import Attendee
from src.entity.table import Table
from src.optimization_layer.print_attendees_assigned_to_tables import print_tables_compressed
from src.optimization_layer.assign_attendees_to_tables import assign_attendees_to_tables

logger: logging.Logger = logging.getLogger(__name__)


def initial_solution(tables: list[Table],
                     attendees: list[Attendee],
                     parameters: Parameters) -> None:
    # for now, find the attribute_type with the most items

    cntr: dict[str, defaultdict] = {attribute_type: defaultdict(int)
                                    for attribute_type in parameters.attribute_field_names}
    for attendee in attendees:
        attendee.assigned_to_table = None
        for attribute_type, item in attendee.attributes.items():
            cntr[attribute_type][item] += 1
    # go through list of attribute types, return the one that maximizes the number of items used of that type
    attribute_max = max(parameters.attribute_field_names, key=lambda attribute: len(cntr[attribute]))

    for item in cntr[attribute_max].keys():
        while True:
            attendees_to_be_assigned = [attendee for attendee in attendees
                                        if attendee.assigned_to_table is None and
                                        attendee.attributes[attribute_max] == item]
            if len(attendees_to_be_assigned) == 0:
                break
            largest_table_size = max(len(table.attendees) for table in tables)
            smallest_table_size = min(len(table.attendees) for table in tables)
            if smallest_table_size == largest_table_size:
                tables_to_be_assigned = {table for table in tables}
            else:
                tables_to_be_assigned = {table for table in tables if len(table.attendees) < largest_table_size}

            attendee_assigned_to_group = assign_attendees_to_tables(attendees_to_be_assigned, tables_to_be_assigned)

            for attendee, table in attendee_assigned_to_group:
                attendee.assigned_to_table = table
                table.add_attendee(attendee)

            # print_tables_compressed(tables)

    return
