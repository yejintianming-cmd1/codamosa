#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2022 Pynguin Contributors
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#

import pytest

from pynguin.analyses.codedeserializer import deserialize_code_to_testcases
from pynguin.generation.export.exportprovider import ExportProvider
from pynguin.setup.testclustergenerator import TestClusterGenerator


# TODO(fk) this is not correct, i.e. in the second example str3 should be dict0 and var0
#  should be list0. However, this is a more complex problem in AST -> Statement
#  conversion.
@pytest.mark.parametrize(
    "testcase_seed",
    [
        (
            """    float_0 = 1.1
    var_0 = module_0.positional_only(float_0)"""
        ),
        (
            """    float_0 = 1.1
    int_0 = 42
    var_0 = []
    str_0 = 'test'
    str_1 = 'key'
    str_2 = 'value'
    str_3 = {str_1: str_2}
    var_1 = module_0.all_params(float_0, int_0, *var_0, param4=str_0, **str_3)"""
        ),
    ],
)
def test_parameter_mapping_roundtrip(testcase_seed, tmp_path):
    testcase_seed = (
        """# Automatically generated by Pynguin.
import tests.fixtures.grammar.parameters as module_0

def test_case_0():
"""
        + testcase_seed
    )
    test_cluster = TestClusterGenerator(
        "tests.fixtures.grammar.parameters"
    ).generate_cluster()
    testcases, _, _ = deserialize_code_to_testcases(testcase_seed, test_cluster)
    export_path = tmp_path / "export.py"
    ExportProvider.get_exporter().export_sequences(export_path, testcases)
    with open(export_path) as f:
        content = f.read()
        assert (
            content == testcase_seed
        ), f"=======\n{content}\n=== differs from ===\n{testcase_seed}"


def test_deserialize_object_not_under_test():
    testcase_seed = """import tests.fixtures.cluster.dependency as module_0
import tests.fixtures.cluster.simple_dependencies as module_1

def test_case_0():
    int_0 = 1
    some_argument_type_0 = module_0.SomeArgumentType(int_0)
    construct_me_with_dependency_0 = module_1.ConstructMeWithDependency(some_argument_type_0)"""
    test_cluster = TestClusterGenerator(
        "tests.fixtures.cluster.simple_dependencies"
    ).generate_cluster()
    testcases, _, _ = deserialize_code_to_testcases(testcase_seed, test_cluster)
    content = ExportProvider.get_exporter().export_sequences_to_str(testcases)
    assert (
        content == testcase_seed
    ), f"=======\n{content}\n=== differs from ===\n{testcase_seed}"


def test_list_literal_wrong_semantics():
    """This regression test reflects the fact that `try_generating_specific_function`
    (in _StatementDeserializer) changes the semantics of list(), set(), etc. functions,
    by putting in the iterable as a literal argument rather than iterating through
    the iterable. There is no way simple way to fix this without supporting a new type
    of statement or doing some complicated reachability analysis.
    """

    # here, int_3 has len 2
    testcase_seed = """def test_case_0():
    int_0 = 0
    int_1 = 1
    int_2 = (int_0, int_1)
    int_3 = list(int_2)"""

    # here, int_3 has len 1
    wrong_semantics_seed = """def test_case_0():
    int_0 = 0
    int_1 = 1
    int_2 = (int_0, int_1)
    int_3 = [int_2]"""

    test_cluster = TestClusterGenerator(
        "tests.fixtures.grammar.parameters"
    ).generate_cluster()

    testcases, _, _ = deserialize_code_to_testcases(testcase_seed, test_cluster)
    content = ExportProvider.get_exporter().export_sequences_to_str(testcases)
    assert (
        content == wrong_semantics_seed
    ), f"=======\n{content}\n=== differs from ===\n{wrong_semantics_seed}"
