import logging
import random
import datetime

from src.parameters.parameters import Parameters
from src.entity.table import Table
from src.optimization_layer.assign_attendees_to_tables import assign_attendees_to_tables
from src.optimization_layer.print_attendees_assigned_to_tables import output_summary
import src.globals as _globals

logger = logging.getLogger(__name__)


def iterate_reoptimization(parameters: Parameters, tables: list[Table]):
    total_score = sum(table.score() for table in tables)
    print(f'Initial solution score: {total_score}')

    if parameters.default_sameness_score == 0.0 and len(parameters.override_sameness_score) == 0:
        pure_quadratic_penalty = True
        # test if initial solution is optimal
        total_penalty_score = sum(table.upper_bound_violations() for table in tables)
        if total_penalty_score == 0:
            logger.info("Found optimal arrangements")
            return
    else:
        pure_quadratic_penalty = False

    for iteration in range(parameters.max_iterations):
        if _globals.stop_execution:
            return
        if (datetime.datetime.now() - _globals.start_time).total_seconds() >= parameters.max_run_time_seconds:
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
            logger.error('new score worse')
        elif new_total_score == total_score:
            logger.info(f'Iteration: {iteration} did not improve score')
        else:
            logger.info(f'Iteration: {iteration} improved score: {new_total_score}')
            logger.info(f'\n{output_summary(parameters, tables)}')
            if pure_quadratic_penalty:
                # if only the quadratic penalty is being used, and if there are no upper-bound violations, then finished
                total_penalty_score = sum(table.upper_bound_violations() for table in tables)
                if total_penalty_score == 0:
                    logger.info("Found optimal arrangements")
                    return

            total_score = new_total_score
