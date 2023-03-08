import random

from src.entity.attendee import Attendee
from src.entity.table import Table

def reoptimize_selected_items(item_in_group: Dict[int, int],
                              groups: Dict[int, List[int]],
                              diversity_score,
                              ubba: UpperBoundByAttribute):
    """item_in_group:  group_number -> item_number"""
    for group_num, item_num in item_in_group.items():
        groups[group_num].remove(item_num)
        attendees[item_num].assigned_to_group = -1
    items_to_be_assigned = list(item_in_group.values())

    attendee_assigned_to_group = assign_items_to_groups(
        items_to_be_assigned, groups, diversity_score, ubba, attendees)
    for item, j in attendee_assigned_to_group:
        attendees[item].assigned_to_group = j
        groups[j].append(item)

    print_groups(attendees, groups)


def iterate_reoptimization(attendees: list[Attendee], tables: list[Table]):
    for iteration in range(500):

        random_attendee_per_table = [random.choice(list(table.attendees)) for table in tables]
        reoptimize_selected_items(random_attendee_per_table, tables)
        total_score, _ = total_scores(groups, diversity_score)

        logger.info(
            f"After refinement iteration {iteration}, total score is {total_score}, penalty score: {total_ub_penalty}")

        if total_ub_penalty < prev_penalty_at_score:
            for attendee in attendees.values():
                attendee.move_assignment_to_best_penalty()

        if total_score > prev_score:
            prev_score = total_score
            prev_penalty_at_score = total_ub_penalty

            # copy to best_assignment
            for attendee in attendees.values():
                attendee.move_assignment_to_best()

            count_at_current_score = 0
        else:
            count_at_current_score += 1
            if total_ub_penalty < prev_penalty_at_score:
                prev_penalty_at_score = total_ub_penalty
                for attendee in attendees.values():
                    attendee.move_assignment_to_best()

        current_time = datetime.datetime.now()
        elapsed_seconds = (current_time - start_time).total_seconds()
        if count_at_current_score > 25 and elapsed_seconds > parameters['max_run_time_seconds']:
            break

    best_groups = {j: [] for j in range(num_groups)}
    for item, attendee in attendees.items():
        best_groups[attendee.best_assignment].append(item)
