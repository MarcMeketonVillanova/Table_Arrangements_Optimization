import random

from src.parameters.parameters import Parameters
from src.entity.table import Table
from src.optimization_layer.assign_attendees_to_tables import assign_attendees_to_tables
from src.optimization_layer.print_attendees_assigned_to_tables import output_summary
import src.globals as globals

def iterate_reoptimization(parameters: Parameters, tables: list[Table]):
    total_score = sum(table.score() for table in tables)
    print(f'Initial solution score: {total_score}')
    for iteration in range(500):
        if globals.stop_execution:
            return
        attendees_to_assign = list()
        for table in tables:
            attendee = random.choice(list(table.attendees))
            attendees_to_assign.append(attendee)
            table.remove_attendee(attendee)

        attendee_assigned_to_group = assign_attendees_to_tables(attendees_to_assign, tables)

        for attendee, table in attendee_assigned_to_group:
            attendee.assigned_to_table = table
            table.add_attendee(attendee)

        new_total_score = sum(table.score() for table in tables)
        if new_total_score > total_score:
            # made it worse.  That should never happen
            print('new score worse')
        elif new_total_score == total_score:
            print(f'Iteration: {iteration} did not improve score')
        else:
            print(f'Iteration: {iteration} improved score: {new_total_score}')
            print(output_summary(parameters, tables))
            total_score = new_total_score
