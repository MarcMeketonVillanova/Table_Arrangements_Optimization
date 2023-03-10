from typing import Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.entity.table import Table


class Attendee:
    class_item_id: int = 0

    def __init__(self, _id: Union[str, int], name: str, attributes: dict[str, str]):
        self.item_id: int = Attendee.class_item_id   # internal to this program
        Attendee.class_item_id += 1
        self.id: Union[str, int] = _id         # comes from data input
        self.name: str = name
        self.attributes: dict[str, str] = attributes
        self.assigned_to_table: Optional[Table] = None
        self.best_assignment: Optional[Table] = None
        self.best_penalty_assignment: Optional[Table] = None

    @property
    def item(self):
        return f'item_{self.item_id}'

    def move_assignment_to_best(self):
        self.best_assignment = self.assigned_to_table

    def move_assignment_to_best_penalty(self):
        self.best_penalty_assignment = self.assigned_to_table

    def __hash__(self):
        return hash(self.item_id)

    def __eq__(self, other):
        if other is not Attendee:
            return False
        return self.item_id == other.item_id

    def __repr__(self):
        return ';'.join(k + ':' + v for k, v in self.attributes.items())
