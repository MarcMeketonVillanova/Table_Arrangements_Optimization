from typing import Collection, List

from src.parameters.parameters import Parameters
from src.entity.attendee import Attendee
from src.entity.table import Table


def initialize_tables(parameters: Parameters, attendees: Collection[Attendee]) -> List[Table]:
    Table.initialize_parameters(parameters, attendees)
    tables = [Table(table_id) for table_id in range(Table.num_tables)]
    print(Table.upper_bound_by_item)
    return tables
