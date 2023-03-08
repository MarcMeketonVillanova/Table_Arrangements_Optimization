from typing import Collection, List
from math import ceil

from src.parameters.parameters import Parameters
from src.entity.attendee import Attendee
from src.entity.table import Table


def initialize_tables(parameters: Parameters, attendees: Collection[Attendee]) -> List[Table]:
    num_attendees = len(attendees)
    num_tables = ceil(num_attendees / parameters.max_group_size)
    Table.initialize_parameters(parameters)
    tables = [Table(table_id) for table_id in range(num_tables)]
    return tables
