from logging import getLogger
from pathlib import Path

from pydantic import ValidationError

from .schema import TestCase, TestGroup

logger = getLogger(__name__)


def get_test_cases_groups_configs(test_dir: Path):
    for test_group_file in test_dir.glob("*/setup.json"):
        if not test_group_file.is_file():
            continue
        try:
            config = TestGroup.model_validate_json(test_group_file.read_text())
            config.set_dir_path(test_group_file.parent)
            yield test_group_file.parent, config
        except ValidationError as error:
            logger.warning(
                f"Validation error, skipping test group {test_group_file} %s\n", error
            )


def get_test_cases_configs(group_dir: Path):
    for test_case_file in group_dir.glob("*/test.json"):
        if not test_case_file.is_file():
            continue
        try:
            config = TestCase.model_validate_json(test_case_file.read_text())
            config.set_dir_path(test_case_file.parent)
            yield test_case_file.parent, config
        except ValidationError as error:
            logger.warning(
                f"Validation error, skipping test case {test_case_file} %s\n",
                error,
            )


def get_tests_groups(test_dir: Path):
    "Finds every test group with every test case in the given `test_dir`."
    test_groups: list[TestGroup] = []
    for group_dir, group_config in get_test_cases_groups_configs(test_dir):
        test_groups.append(group_config)
        for test_dir, test_config in get_test_cases_configs(group_dir):
            group_config.add_test(test_config)
    return test_groups
