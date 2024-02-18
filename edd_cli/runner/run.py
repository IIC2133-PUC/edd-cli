from pathlib import Path

from ..schema.results import TestErrorResult, TestGroupErrorResults, TestGroupOkResults
from ..schema.tests import TestGroup
from .environment import Environment
from .runners import AbstractRunner, RunErrorException
from .temp_dirs import TempDirGenerator


class Orchestrator:
    def __init__(
        self, repo_path: Path, runner: AbstractRunner, dir_generator: TempDirGenerator
    ):
        self._repo_path = repo_path
        self._runner = runner
        self._dir_generator = dir_generator
        self._assignments_results: list[TestGroupErrorResults | TestGroupOkResults] = []

    def _create_env(self):
        return Environment(self._repo_path, self._runner, self._dir_generator)

    def run(self, test_groups: list[TestGroup]):
        for g in self.iter_run_assignment_group(test_groups):
            for t in g.iter_run_group_test():
                pass
        return self.assignment_results

    def iter_run_assignment_group(self, test_groups: list[TestGroup]):
        "Iter intermediate function, useful when login progress."
        for group in test_groups:
            environment = self._create_env()
            try:
                environment.run_stages(group)
                result = TestGroupOkResults(name=group.display_name)
                self._assignments_results.append(result)
                yield OrchestratorForGroup(result, group, environment)
            except RunErrorException as exception:
                result = TestGroupErrorResults(
                    name=group.display_name, error=exception.message
                )
                self._assignments_results.append(result)
                yield OrchestratorForGroup(result, group, environment)

    @property
    def assignment_results(self):
        return self._assignments_results


class OrchestratorForGroup:
    def __init__(
        self,
        result: TestGroupOkResults | TestGroupErrorResults,
        group: TestGroup,
        env: Environment,
    ):
        self._group_result = result
        self._group = group
        self._env = env

    @property
    def result(self):
        return self._group_result

    @property
    def name(self):
        return self._group.display_name

    @property
    def tests(self):
        return self._group.tests

    def iter_run_group_test(self):
        if not isinstance(self._group_result, TestGroupOkResults):
            raise ValueError("Can't run tests on a errored group result")

        for test in self._group.tests:
            test_env = self._env.clone()
            try:
                test_env.run_stages(test)
                test_result = test_env.get_result()
                self._group_result.results.append(test_result)
                yield test_result
            except RunErrorException as exception:
                test_result = TestErrorResult(
                    name=test.display_name, error=exception.message
                )
                self._group_result.results.append(test_result)
                yield test_result
