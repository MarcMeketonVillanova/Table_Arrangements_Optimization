import os
from pathlib import Path
import yaml
from yaml.scanner import ScannerError


class Parameters:
    def __init__(self, path_to_yaml=r"../../data_and_log_files/config.yml"):
        """Read the config.yml configuration file and use it to populate the Parameters object"""

        # set default values, which will be overwritten once the yml file is read
        # PyCharm also uses the below for 'intellisense'
        self.max_table_size: int = 10
        self.id_field_name: str = 'ID'
        self.name_field_name: str = 'Name'
        self.attribute_field_names: list[str] = ['Office', 'Role', 'Start_Class', 'Gender']
        self.default_quadratic_penalty: float = 1.0
        self.override_quadratic_penalty: dict[str, float] = dict()
        self.default_sameness_score: float = 0.0
        self.override_sameness_score: list[tuple[str, str, str, str, float]] = list()
        self.max_run_time_seconds: int = 300
        self.max_iterations: int = 500

        # location of directories and files
        self.data_directory: Path = Path(r'..\..\data_and_log_files')

        # names of files in the data_directory
        self.attendee_file_name = 'attendees.csv'
        self.log_file_name = 'log.txt'
        self.table_assignments_file_name = 'table_assignments.csv'
        self.table_summary_statistics = 'table_summary.csv'

        try:
            if path_to_yaml is not None and os.path.exists(path_to_yaml):
                self.__dict__ = yaml.safe_load(open(path_to_yaml))
            else:
                raise ValueError(f'File {path_to_yaml} does not exist')
        except ScannerError as exc:
            msg = "Error while parsing YAML file:\n"
            if hasattr(exc, 'problem_mark'):
                if exc.context is not None:
                    msg += ('  parser says\n' + str(exc.problem_mark) + '\n  ' +
                            str(exc.problem) + ' ' + str(exc.context) +
                            '\nPlease correct data and retry.')
                else:
                    msg += ('  parser says\n' + str(exc.problem_mark) + '\n  ' +
                            str(exc.problem) + '\nPlease correct data and retry.')
            raise Exception(msg)

        # Sanity checks
        self.attribute_field_names = [field_name.strip()
                                      for field_name in self.attribute_field_names]
        override_fields_not_found = [attribute_name
                                     for attribute_name in self.override_quadratic_penalty.keys()
                                     if attribute_name not in self.attribute_field_names]
        if len(override_fields_not_found) > 0:
            raise Exception('"override_quadratic_penalty" includes fields not in attribute_field_names: '
                            f'{override_fields_not_found}')

        override_different_score = list()
        override_issues = ""
        for override in self.override_sameness_score:
            if len(override) != 5:
                override_issues += 'Expected an override in the form [attribute, item, attribute, item, score]'
                f', received {override}\n'
                continue
            attribute1, item1, attribute2, item2, score = override
            if attribute1 not in self.attribute_field_names:
                override_issues += f'  - attribute name {attribute1} not found in attribute_field_names\n'
            if attribute2 not in self.attribute_field_names:
                override_issues += f'  - attribute name {attribute2} not found in attribute_field_names\n'
            try:
                override_score = float(score)
            except ValueError:
                override_issues += f'Could not convert score {score} to a float'
            override_different_score.append(tuple(override))
        if len(override_issues) > 0:
            msg = 'Illegal overrides.  Expected a list of 5-element list, each one of the form ' \
                  '[attribute, item, attribute, item, score]\n'
            raise ValueError(msg + override_issues)
        self.override_sameness_score = override_different_score

        self.data_directory = Path(self.data_directory)

    def display(self) -> str:
        result = f"{'Parameter':40s}{'Type':25s}{'Value':50s}\n"
        for k, v in self.__dict__.items():
            result += f"{k:40s}{str(type(v)):25s}{str(v):50s}\n"
        return result


if __name__ == '__main__':
    parameters = Parameters()
    parameters.display()
