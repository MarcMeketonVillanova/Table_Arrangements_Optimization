from typing import List, Tuple, Dict, Any, Union
from dataclasses import dataclass
import logging
import argparse

import signal
import math
import random
import datetime

from collections import Counter, defaultdict

import yaml
import pandas as pd
import numpy as np
import networkx as nx


@dataclass
class Attendee:
    item_id: int       # internal to this program
    id: int         # comes from data input
    name: str
    role: str
    office: str
    gender: str
    start_year: str
    assigned_to_group: int = -1
    best_assignment: int = -1
    best_penalty_assignment: int = -1

    @property
    def item(self):
        return 'item_' + str(self.item_id)

    def move_assignment_to_best(self):
        self.best_assignment = self.assigned_to_group

    def move_assignment_to_best_penalty(self):
        self.best_penalty_assignment = self.assigned_to_group

    def __repr__(self):
        attributes = self.role[0] + self.role[2] + "-" + self.office[0] + "-" + self.start_year[0] + "-" + self.gender
        return attributes


class UpperBoundByAttribute:
    def __init__(self):
        self.role_upper_bound: Dict[str, float] = dict()
        self.office_upper_bound: Dict[str, float] = dict()
        self.start_year_upper_bound: Dict[Union[str, int], float] = dict()
        self.gender_upper_bound: Dict[str, float] = dict()

    # noinspection PyShadowingNames
    def zero_grp_count(self, num_groups: int) -> Dict[int, Dict[str, Dict[Union[str, int], float]]]:
        attribute_by_group_counts = {j: {'ROLE': {attribute: 0.0 for attribute in self.role_upper_bound.keys()}} |
                                     {'OFFICE': {attribute: 0.0 for attribute in self.office_upper_bound.keys()}} |
                                     {'START_YEAR': {attribute: 0.0
                                                     for attribute in self.start_year_upper_bound.keys()}} |
                                     {'GENDER': {attribute: 0.0 for attribute in self.gender_upper_bound.keys()}}
                                     for j in range(num_groups)}
        return attribute_by_group_counts

    # noinspection PyShadowingNames
    def total_upper_bound_penalty(self, attribute_by_group_count: Dict[int, Dict[str, Dict[str, float]]]) \
            -> Tuple[float, Dict[int, float]]:
        penalty_by_group = {j: 0.0 for j in attribute_by_group_count.keys()}
        for role_attribute, count in self.role_upper_bound.items():
            for j in penalty_by_group.keys():
                penalty_by_group[j] += 10.0 if attribute_by_group_count[j]['ROLE'][role_attribute] > count else 0
        for office_attribute, count in self.office_upper_bound.items():
            for j in penalty_by_group.keys():
                penalty_by_group[j] += 5.0 if attribute_by_group_count[j]['OFFICE'][office_attribute] > count else 0
        for start_year_attribute, count in self.start_year_upper_bound.items():
            for j in penalty_by_group.keys():
                penalty_by_group[j] += (2.0 if attribute_by_group_count[j]['START_YEAR'][start_year_attribute] > count
                                        else 0)
        for gender_attribute, count in self.gender_upper_bound.items():
            for j in penalty_by_group.keys():
                penalty_by_group[j] += 10.0 if attribute_by_group_count[j]['GENDER'][gender_attribute] > count else 0

        total_ub_penalty = sum(penalty_by_group.values())

        if total_ub_penalty > 0:
            for j in penalty_by_group.keys():
                if attribute_by_group_count[j]['ROLE'][attendee.role] > self.role_upper_bound[attendee.role]:
                    logger.info(f'penalty group {j}, role {attendee.role}')
                if attribute_by_group_count[j]['OFFICE'][attendee.office] > self.office_upper_bound[attendee.office]:
                    logger.info(f'penalty group {j}, office {attendee.office}')
                if (attribute_by_group_count[j]['START_YEAR'][attendee.start_year] >
                        self.start_year_upper_bound[attendee.start_year]):
                    logger.info(f'penalty group {j}, hire {attendee.start_year}')
                if attribute_by_group_count[j]['GENDER'][attendee.gender] > self.gender_upper_bound[attendee.gender]:
                    logger.info(f'penalty group {j}, gender {attendee.gender}')

        return total_ub_penalty, penalty_by_group

    # noinspection PyShadowingNames
    def upper_bound_penalty(self,
                            item: int, groups: Dict[int, List[int]],
                            attendees: Dict[int, Attendee]) -> Dict[int, float]:
        """If item is placed in group, what penalty do we have for violating upper bounds"""

        grp_counts = self.attribute_counts_by_group(num_groups, groups, attendees)
        attendee = attendees[item]
        penalty_scores = dict()
        for j in range(num_groups):
            penalty = 0.0
            # if the existing count for the attendee's role is already at the upper bound
            #   then putting that attendee into the group would violate the upper bound
            penalty += (10.0 if grp_counts[j]['ROLE'][attendee.role] >= self.role_upper_bound[attendee.role] else 0)
            penalty += (5.0 if grp_counts[j]['OFFICE'][attendee.office] >= self.office_upper_bound[attendee.office]
                        else 0)
            penalty += (2.0 if grp_counts[j]['START_YEAR'][attendee.start_year] >=
                               self.start_year_upper_bound[attendee.start_year] else 0)
            penalty += (10.0 if grp_counts[j]['GENDER'][attendee.gender] >= self.gender_upper_bound[attendee.gender]
                             else 0)

            penalty_scores[j] = penalty
        return penalty_scores

    # noinspection PyShadowingNames
    def attribute_counts_by_group(self, num_groups: int,
                                  groups: Dict[int, List[int]],
                                  attendees: Dict[int, Attendee]) -> Dict[int, Dict[str, Dict[Union[str, int], float]]]:
        """Returns XX where XX[13]['ROLE']['PTR'] is the number of partners (a role attribute) already in group 13

        Also note that groups may (intentionally) be missing an item
        """

        attribute_by_group_counts = self.zero_grp_count(num_groups)

        for j, grp in groups.items():
            for item in grp:
                attendee = attendees[item]
                attribute_by_group_counts[j]['ROLE'][attendee.role] += 1.0
                attribute_by_group_counts[j]['OFFICE'][attendee.office] += 1.0
                attribute_by_group_counts[j]['START_YEAR'][attendee.start_year] += 1.0
                attribute_by_group_counts[j]['GENDER'][attendee.gender] += 1.0
        return attribute_by_group_counts


# noinspection PyShadowingNames
def setup_logger(output_dir: str):
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


# noinspection PyShadowingNames
def calculate_diversity_scores(attendees: Dict[int, Attendee],
                               parameters: Dict[str, Any],
                               role_scores: Dict[Tuple[str, str], float],
                               office_scores: Dict[Tuple[str, str], float]) -> np.array:
    diversity_score = np.zeros([num_items, num_items])
    different_gender_score = parameters['different_gender_score']
    different_start_class_year_score = parameters['different_start_class_year_score']

    # Two choices for consultants used for developing the 'start_year' score
    #   When the 'start_year' is an actual year, this score should apply to the 'real' consultants (ACG, CCG)
    #   and not to the support or partners or specialist
    #   When the 'start_year' is either 'PRE_COVID_JOINER' or 'COVID_JOINER', the score should apply to all

    # consultants = {'CCG', 'ACG'}
    consultants = set(role_1 for role_1, _ in role_scores.keys())
    for idx_row in range(num_items):
        diversity_score[idx_row, idx_row] = 0.0
        for idx_col in range(idx_row+1, num_items):
            item_1 = attendees[idx_row]
            item_2 = attendees[idx_col]
            score = 0.0
            score += role_scores[(item_1.role, item_2.role)]
            score += 0 if item_1.gender == item_2.gender else different_gender_score
            score += office_scores[(item_1.office, item_2.office)]
            if item_1.role in consultants and item_2.role in consultants:
                if item_1.start_year != item_2.start_year:
                    score += different_start_class_year_score
            diversity_score[idx_row, idx_col] = score
            diversity_score[idx_col, idx_row] = score
    return diversity_score


# noinspection PyShadowingNames
def price_out_item_in_existing_group(item: int,
                                     groups: Dict[int, List[int]],
                                     diversity_score: np.array) -> Dict[int, float]:
    group_scores = {j: 99999.0 if len(grp) == 0 else sum(diversity_score[item, item_in_group] for item_in_group in grp)
                    for j, grp in groups.items()}
    return group_scores


# noinspection PyShadowingNames
def assign_items_to_groups(items: List[int],
                           groups: Dict[int, List[int]],
                           diversity_score: np.array,
                           ubba: Union[UpperBoundByAttribute, None],
                           attendees: Dict[int, Attendee]) -> List[Tuple[int, int]]:
    g = nx.DiGraph()

    items_to_be_assigned = [item for item in items if attendees[item].assigned_to_group == -1]
    m = len(items_to_be_assigned)
    n = len(groups)

    for item in items_to_be_assigned:
        attendee = attendees[item]
        g.add_node(attendee.item, attendee=attendee, demand=-1)
    for j in groups.keys():
        g.add_node('group_' + str(j), group=j, demand=1)
    g.add_node('Fake', demand=m - n)

    for item in items_to_be_assigned:
        attendee = attendees[item]
        scores = price_out_item_in_existing_group(item, groups, diversity_score)

        if ubba is not None:
            penalty_scores = ubba.upper_bound_penalty(item, groups, attendees)
        else:
            penalty_scores = {j: 0.0 for j in groups.keys()}

        for j in groups.keys():
            g.add_edge(attendee.item, 'group_' + str(j), weight=-scores[j] + penalty_scores[j])

    if m < n:
        for j in groups.keys():
            g.add_edge('Fake', 'group_' + str(j), weight=0.0)
    else:
        for item in items_to_be_assigned:
            attendee = attendees[item]
            g.add_edge(attendee.item, 'Fake', weight=0.0)
    # with open(r'c:/temp/edges.txt','w') as ff:
    #     ff.write(str(g.edges.data()))

    flows = nx.min_cost_flow(g, demand='demand', weight='weight')

    attendee_assigned_to_group: List[Tuple[int, int]] = []
    for from_node, to_nodes in flows.items():
        if from_node[:4] == "item":
            # should be exactly one to_node with positive value
            attendee = g.nodes[from_node]['attendee']
            to_node = [_to_node for _to_node, value in to_nodes.items() if value > 0.01][0]
            if to_node[:5] == 'group':
                attendee_assigned_to_group.append((attendee.item_id, g.nodes[to_node]['group']))

    return attendee_assigned_to_group


# noinspection PyShadowingNames
def initial_solution(num_groups: int,
                     role_summary,
                     attendees: Dict[int, Attendee],
                     diversity_score,
                     ubba: UpperBoundByAttribute) -> Dict[int, List[int]]:
    groups = {j: [] for j in range(num_groups)}
    for attendee in attendees.values():
        attendee.assigned_to_group = -1
    for role, _ in role_summary:
        while True:
            items_to_be_assigned = [item for item in attendees_by_role[role]
                                    if attendees[item].assigned_to_group == -1]
            if len(items_to_be_assigned) == 0:
                break
            largest_group_size = max(len(grp) for grp in groups.values())
            smallest_group_size = min(len(grp) for grp in groups.values())
            if smallest_group_size == largest_group_size:
                groups_to_be_assigned = {j: grp for j, grp in groups.items()}
            else:
                groups_to_be_assigned = {j: grp for j,
                                         grp in groups.items() if len(grp) < largest_group_size}

            attendee_assigned_to_group = assign_items_to_groups(
                items_to_be_assigned, groups_to_be_assigned, diversity_score, ubba, attendees)

            for item, j in attendee_assigned_to_group:
                attendees[item].assigned_to_group = j
                groups[j].append(item)

            print_groups(attendees, groups)

        attribute_by_group_count = ubba.attribute_counts_by_group(num_groups, groups, attendees)

        total_ub_penalty, _ = ubba.total_upper_bound_penalty(attribute_by_group_count)
        logger.info(f"Initial assignment of role: {role}, penalty: {total_ub_penalty}")
    return groups


# noinspection PyShadowingNames
def print_groups(attendees, groups):
    groups_to_print = {j + 1: ', '.join(str(attendees[item]) for item in group) for j, group in groups.items()}
    logger.info("Table\tAttendee")
    for jp1, grp_to_print in groups_to_print.items():
        logger.info(f"{jp1}\t{grp_to_print}")


# noinspection PyShadowingNames
def total_scores(groups: Dict[int, List[int]], diversity_score: np.array) -> Tuple[float, Dict[int, float]]:
    group_scores = {j: sum(diversity_score[item_1, item_2]
                           for item_1 in grp for item_2 in grp) for j, grp in groups.items()}
    total_score = sum(group_scores.values())
    return total_score, group_scores


# noinspection PyShadowingNames
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

# noinspection PyShadowingNames
def output_solution(attendees: Dict[int, Attendee], groups: Dict[int, List[int]], csv_dir: str) -> None:
    item_to_group = {item: j for j, grp in groups.items() for item in grp}
    table_assignments_dict_for_pd = {
        "GROUP": [item_to_group[item] + 1 for item in attendees.keys()],
        "NAME": [attendee.name for attendee in attendees.values()],
        "ROLE": [attendee.role for attendee in attendees.values()],
        "OFFICE": [attendee.office for attendee in attendees.values()],
        "START_YEAR": [attendee.start_year for attendee in attendees.values()],
        "GENDER": [attendee.gender for attendee in attendees.values()]
    }

    table_assignments_df = pd.DataFrame(table_assignments_dict_for_pd).sort_values(
        by=['GROUP', 'ROLE', 'OFFICE', 'GENDER', 'START_YEAR', 'NAME'])
    table_assignments_df.to_csv(csv_dir + 'table_assignments.csv', index=False, mode='w')


# noinspection PyShadowingNames
def output_summary(attendees: Dict[int, Attendee],
                   groups: Dict[int, List[int]],
                   ubba: UpperBoundByAttribute,
                   csv_dir: str) -> None:
    item_to_group = {item: j for j, grp in groups.items() for item in grp}
    attendee_dict_for_pd = {"ID": [attendee.item_id for attendee in attendees.values()],
                            "Group": [item_to_group[item] for item in attendees.keys()],
                            "Role": [attendee.role for attendee in attendees.values()],
                            "Office": [attendee.office for attendee in attendees.values()],
                            "Start_Year": ["SY_" + str(attendee.start_year) for attendee in attendees.values()],
                            "Gender": [attendee.gender for attendee in attendees.values()]}

    attendee_solution_df = pd.DataFrame(attendee_dict_for_pd).sort_values(by=['Group'])

    _, group_scores = total_scores(groups, diversity_score)

    attribute_by_group_count = ubba.attribute_counts_by_group(num_groups, groups, attendees)
    _, penalty_scores = ubba.total_upper_bound_penalty(attribute_by_group_count)

    group_scores_df = pd.DataFrame({"Group": [j for j in group_scores.keys()],
                                    "Score": [score for score in group_scores.values()],
                                    "Penalty": [penalty for penalty in penalty_scores.values()],
                                    "Table_Size": [len(grp) for grp in groups.values()]})
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
    summary_df.to_csv(csv_dir + 'summary.csv', index=False)


def ctrl_c_handler(_signum, _frame):
    """When ctrl-c is pressed, wait till next re-optimization occurs and write out best answer then exit"""
    global stop_executing
    stop_executing = True
    logger.info("Control-C was pressed.  Will stop optimizing and output best solution so far")


# Program starts here
start_time = datetime.datetime.now()

stop_executing = False
signal.signal(signal.SIGINT, ctrl_c_handler)

parser = argparse.ArgumentParser()
parser.add_argument("--config_location", type=str, help="YAML configuration file location - full file path",
                    default='C:/DocumentsOliverWyman/CCG_Grouping_Model/TMP_FILES/config.yml')
args = parser.parse_args()

# Read in configuration file
yaml_file_location = args.config_location
parameters = yaml.load(open(yaml_file_location), Loader=yaml.Loader)
parameters['csv_dir'] += '' if parameters['csv_dir'][-1] in {'\\', '/'} else r'/'
print(parameters)

logger = setup_logger(parameters['csv_dir'] + "log.txt")

logger.info("Telling control file Python is running")
with open(parameters['csv_dir'] + 'control.txt', 'w') as control_file:
    control_file.write('RUNNING\n')

# read in attendees
attendee_df = pd.read_csv(parameters['csv_dir'] + 'Attendee_Table.csv')
logger.info(attendee_df)
attendee_df['Start_Class'].fillna("PRE_COVID_JOINER", inplace=True)
attendees = {idx: Attendee(idx, row.ID, row.Name, row.Role, row.Office, row.Gender, row.Start_Class)
             for idx, row in enumerate(attendee_df.itertuples(index=False))}

# validate input
duplicated_id = attendee_df[attendee_df.duplicated(
    subset=['ID'], keep=False)].sort_values(by=['ID', 'Name'])
if len(duplicated_id) > 0:
    logger.error(
        f"Read in {len(attendee_df)} attendees and found duplicate ID's.  Duplicates are:")
    logger.error(duplicated_id)

# make sure gender is either M or F (hopefully will not get into trouble here!)
if not attendee_df['Gender'].isin(['M', 'F']).all():
    logger.error(
        f'Some genders are not "M" or "F", all found genders are: {attendee_df["Gender"].unique()}')

# read in role score matrix
role_scores_np = (
    pd.read_csv(parameters['csv_dir'] + 'Role_Scores.csv')
    .melt(id_vars='ROLE', var_name='Role2', value_name='Score')
    .rename({'ROLE': 'Role1'}, axis='columns')
    .dropna()
    .to_numpy()
)
role_scores: Dict[Tuple[str, str], float] = dict()
for idx_row in range(role_scores_np.shape[0]):
    role_scores[(role_scores_np[idx_row, 0], role_scores_np[idx_row, 1])
                ] = role_scores_np[idx_row, 2]
    role_scores[(role_scores_np[idx_row, 1], role_scores_np[idx_row, 0])
                ] = role_scores_np[idx_row, 2]

# read in office score matrix
office_scores_np = (
    pd.read_csv(parameters['csv_dir'] + 'Office_scores.csv')
    .melt(id_vars='Office', var_name='Office2', value_name='Score')
    .rename({'Office': 'Office1'}, axis='columns')
    .dropna()
    .to_numpy()
)
office_scores: Dict[Tuple[str, str], float] = dict()
for idx_row in range(office_scores_np.shape[0]):
    office_scores[(office_scores_np[idx_row, 0], office_scores_np[idx_row, 1])
                  ] = office_scores_np[idx_row, 2]
    office_scores[(office_scores_np[idx_row, 1], office_scores_np[idx_row, 0])
                  ] = office_scores_np[idx_row, 2]

logger.info("Read in data")

num_items = len(attendees)
max_group_size: int = parameters['max_group_size']
min_group_size: int = parameters['min_group_size']
num_groups = math.ceil(num_items / max_group_size)

role_upper_bound_df = attendee_df[['Role']].value_counts().to_frame().rename(columns={0: 'COUNT'})
office_upper_bound_df = attendee_df[['Office']
                                    ].value_counts().to_frame().rename(columns={0: 'COUNT'})
start_year_upper_bound_df = attendee_df[['Start_Class']
                                        ].value_counts().to_frame().rename(columns={0: 'COUNT'})
gender_upper_bound_df = attendee_df[['Gender']
                                    ].value_counts().to_frame().rename(columns={0: 'COUNT'})

role_upper_bound_df['AVERAGE_PER_TABLE'] = role_upper_bound_df['COUNT'] / num_groups
office_upper_bound_df['AVERAGE_PER_TABLE'] = office_upper_bound_df['COUNT'] / num_groups
start_year_upper_bound_df['AVERAGE_PER_TABLE'] = start_year_upper_bound_df['COUNT'] / num_groups
gender_upper_bound_df['AVERAGE_PER_TABLE'] = gender_upper_bound_df['COUNT'] / num_groups

slack_for_rounding_up = 0.1
role_upper_bound_df['UBOUND'] = np.ceil(slack_for_rounding_up + role_upper_bound_df['AVERAGE_PER_TABLE'])
office_upper_bound_df['UBOUND'] = np.ceil(slack_for_rounding_up + office_upper_bound_df['AVERAGE_PER_TABLE'])
start_year_upper_bound_df['UBOUND'] = np.ceil(slack_for_rounding_up + start_year_upper_bound_df['AVERAGE_PER_TABLE'])
gender_upper_bound_df['UBOUND'] = np.ceil(slack_for_rounding_up + gender_upper_bound_df['AVERAGE_PER_TABLE'])

logger.info(f"Role bounds:\n{role_upper_bound_df}")
logger.info(f"Office bounds:\n{office_upper_bound_df.head(15)}")
logger.info(f"Start year bounds:\n{start_year_upper_bound_df}")
logger.info(f"Gender bounds:\n{gender_upper_bound_df}")

ubba = UpperBoundByAttribute()
ubba.role_upper_bound = {row.Index[0]: row.UBOUND for row in role_upper_bound_df.itertuples()}
ubba.office_upper_bound = {row.Index[0]: row.UBOUND for row in office_upper_bound_df.itertuples()}
ubba.start_year_upper_bound = {
    row.Index[0]: row.UBOUND for row in start_year_upper_bound_df.itertuples()}
ubba.gender_upper_bound = {row.Index[0]: row.UBOUND for row in gender_upper_bound_df.itertuples()}

diversity_score = calculate_diversity_scores(attendees, parameters, role_scores, office_scores)

if num_items < num_groups * min_group_size:
    msg = (f"With {num_items} items and max group size of {max_group_size},\n"
           f"Min Group Size must be no larger than {int(num_items / num_groups)}\n"
           f"Using Min Group Size of {int(num_items / num_groups)}\n"
           f"Instead of {min_group_size} found in the Parameters sheet")
    logger.warning(msg)
    min_group_Size = int(num_items / num_groups)
else:
    msg = (f"Num items: {num_items}, Num groups: {num_groups}, Max group size: {max_group_size}, "
           f"Min group size: {min_group_size}")
    logger.info(msg)

role_summary = sorted(((role, count) for role, count in Counter(
    [attendee.role for attendee in attendees.values()]).items()), key=lambda x: (x[1], x[0]))

attendees_by_role = defaultdict(list)
for item, attendee in attendees.items():
    attendees_by_role[attendee.role].append(item)

groups = initial_solution(num_groups, role_summary, attendees, diversity_score, ubba)
total_score, group_scores = total_scores(groups, diversity_score)

attribute_by_group_count = ubba.attribute_counts_by_group(num_groups, groups, attendees)
total_ub_penalty, _ = ubba.total_upper_bound_penalty(attribute_by_group_count)

logger.info(
    f"After initial solution, Total score: {total_score}, penalty score: {total_ub_penalty}")

for attendee in attendees.values():
    attendee.move_assignment_to_best()

prev_score = total_score
prev_penalty_at_score = total_ub_penalty
best_penalty = total_ub_penalty
count_at_current_score = 0
for iteration in range(500):
    if stop_executing:
        break

    item_in_group = {j: random.choice(group) for j, group in groups.items()}
    reoptimize_selected_items(item_in_group, groups, diversity_score, ubba)
    total_score, _ = total_scores(groups, diversity_score)

    attribute_by_group_count = ubba.attribute_counts_by_group(num_groups, groups, attendees)
    total_ub_penalty, _ = ubba.total_upper_bound_penalty(attribute_by_group_count)

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

output_solution(attendees, best_groups, parameters['csv_dir'])
output_summary(attendees, best_groups, ubba, parameters['csv_dir'])

# explicitly close the control file, else timing might confuse the VB module that checks for this.
control_file = open(parameters['csv_dir'] + 'control.txt', 'a')
control_file.write('FINISHED\n')
control_file.close()

logger.info("Finished")
