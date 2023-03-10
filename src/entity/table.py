from typing import Iterable, Collection
from collections import defaultdict
from math import ceil

import pandas as pd

from src.parameters.parameters import Parameters
from src.entity.attendee import Attendee


class Table:
    attribute_type_weights: dict[str, float] = dict()
    attribute_types: Iterable[str] = list()
    default_different_score: float = 0.0
    override_different_score: dict[tuple[str, str, str, str], float] = dict()
    num_tables: int = 0
    upper_bound_by_item: dict[str, dict[str, int]] = dict()
    attribute_counter: dict[str, defaultdict] = dict()

    @classmethod
    def initialize_parameters(cls, parameters: Parameters, attendees: Collection[Attendee]):
        cls.default_different_score = parameters.default_sameness_score
        cls.attribute_types = parameters.attribute_field_names.copy()
        cls.attribute_type_weights = {attribute_name: parameters.default_quadratic_penalty
                                      if attribute_name not in parameters.override_quadratic_penalty
                                      else parameters.override_quadratic_penalty[attribute_name]
                                      for attribute_name in cls.attribute_types}
        for attribute_type_1, item1, attribute_type_2, item2, score in parameters.override_sameness_score:
            cls.override_different_score[(attribute_type_1, item1,
                                          attribute_type_2, item2)] = score

        num_attendees = len(attendees)
        cls.num_tables = ceil(num_attendees / parameters.max_table_size)

        cls.attribute_counter: dict[str, defaultdict] = {attribute_type: defaultdict(int)
                                                         for attribute_type in parameters.attribute_field_names}
        for attendee in attendees:
            attendee.assigned_to_table = None
            for attribute_type, item in attendee.attributes.items():
                cls.attribute_counter[attribute_type][item] += 1

        cls.upper_bound_by_item: dict[str, dict[str, int]] = {attribute_name: {item: ceil(count / cls.num_tables)
                                                                               for item, count in cls.attribute_counter[
                                                                                   attribute_name].items()}
                                                              for attribute_name, item_counts in
                                                              cls.attribute_counter.items()}

    @classmethod
    def build_upper_bound_df(cls) -> pd.DataFrame:
        df = pd.DataFrame({'Upper_Bound': [upper_bound
                                           for attribute_name, upper_bounds in cls.upper_bound_by_item.items()
                                           for item, upper_bound in upper_bounds.items()]},
                          index=[[attribute_name for attribute_name, upper_bounds in cls.upper_bound_by_item.items()
                                  for _ in upper_bounds.keys()],
                                 [item for attribute_name, upper_bounds in cls.upper_bound_by_item.items()
                                  for item in upper_bounds.keys()]
                                 ])

        return df

    def __init__(self, table_id: int):
        self.table_id = table_id

        self.attendees: set[Attendee] = set()
        # number of people at the table with specific attribute (e.g. Princeton) by attribute_type (e.g. Office)
        self.num_by_attribute_value: dict[str, defaultdict[str, int]] = {attribute_name: defaultdict(int)
                                                                         for attribute_name in Table.attribute_types}

    def add_attendee(self, attendee: Attendee):
        if attendee in self.attendees:
            raise ValueError('Attendee already at table')
        self.attendees.add(attendee)
        attendee.assigned_to_table = self
        for attribute_type, attribute in attendee.attributes.items():
            self.num_by_attribute_value[attribute_type][attribute] += 1

    def remove_attendee(self, attendee: Attendee):
        if attendee not in self.attendees:
            raise AttributeError('Trying to remove an attendee not at a table')
        self.attendees.remove(attendee)
        attendee.assigned_to_table = None
        for attribute_type, attribute in attendee.attributes.items():
            self.num_by_attribute_value[attribute_type][attribute] -= 1

    def upper_bound_violations(self) -> float:
        penalty = sum(max(0, count - Table.upper_bound_by_item[attribute_name][item])
                      for attribute_name, item_counts in self.num_by_attribute_value.items()
                      for item, count in item_counts.items()
                      )
        return penalty

    def score(self) -> float:
        penalty_score = 0.0
        for attribute_type, attribute_count in self.num_by_attribute_value.items():
            attribute_type_weight = Table.attribute_type_weights[attribute_type]
            for count in attribute_count.values():
                penalty_score += attribute_type_weight * count * count
        for attendee1 in self.attendees:
            for attendee2 in self.attendees:
                if attendee1.item_id > attendee2.item_id:
                    continue
                for attribute_type_1 in Table.attribute_types:
                    if attendee1.attributes[attribute_type_1] == attendee2.attributes[attribute_type_1]:
                        penalty_score += Table.default_different_score
                    for attribute_type_2 in Table.attribute_types:
                        a_tuple = (attribute_type_1, attendee1.attributes[attribute_type_1],
                                   attribute_type_2, attendee2.attributes[attribute_type_2])
                        if a_tuple in Table.override_different_score:
                            penalty_score += Table.override_different_score[a_tuple]
                        a_tuple = (attribute_type_2, attendee2.attributes[attribute_type_2],
                                   attribute_type_1, attendee1.attributes[attribute_type_1])
                        if a_tuple in Table.override_different_score:
                            penalty_score += Table.override_different_score[a_tuple]
        return penalty_score

    def score_if_attendee_is_added_to_table(self, attendee: Attendee) -> float:
        self.add_attendee(attendee)
        score = self.score()
        self.remove_attendee(attendee)
        return score

    def __hash__(self):
        return hash(self.table_id)

    def __eq__(self, other):
        if other is not Table:
            return False
        return self.table_id == other.table_id

    def __repr__(self):
        return f'Table_{self.table_id + 1}({len(self.attendees)})'
