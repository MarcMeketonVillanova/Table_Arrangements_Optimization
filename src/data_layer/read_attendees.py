import logging
import pandas as pd

from src.parameters.parameters import Parameters
from src.entity.attendee import Attendee

logger = logging.getLogger(__name__)


def read_attendees(parameters: Parameters) -> list[Attendee]:
    attendees_df = pd.read_csv(parameters.data_directory / parameters.attendee_file_name)

    # sanity check
    columns = set(attendees_df.columns)
    errors_found = False
    if parameters.id_field_name not in columns:
        logger.error(f'ID field {parameters.id_field_name} is not found in attendee file')
        errors_found = True

    if parameters.name_field_name not in columns:
        logger.error(f'Name field {parameters.name_field_name} is not found in attendee file')
        errors_found = True

    for attribute_name in parameters.attribute_field_names:
        if attribute_name not in columns:
            logger.error(f'Attribute {attribute_name} is not found in attendee file')
            errors_found = True

    assert not errors_found, "Attendee file did not have the expected columns"

    attendee_list = []
    for row in attendees_df.itertuples(index=False):
        # noinspection PyProtectedMember
        row_as_dict = row._asdict()
        attributes_used = {k.strip(): v.strip()
                           for k, v in row_as_dict.items()
                           if k.strip() in parameters.attribute_field_names}
        attendee = Attendee(row_as_dict[parameters.id_field_name],
                            row_as_dict[parameters.name_field_name],
                            attributes_used)
        attendee_list.append(attendee)

    return attendee_list
