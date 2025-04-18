# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the License);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an AS IS BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""external_file_lib relies on external python libraries non-dependent on g3.

It contains helper methods to run this validator outside of g3.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from yamlformat.validator import base_lib
from yamlformat.validator import findings_lib
from yamlformat.validator import presubmit_validate_types_lib


def Validate(
    filter_text,
    original_directory,
    changed_directory,
    interactive=True,
    require_type_guids=True,
):
  """Validates two directory paths of a diff of ontology versions.

  if the user didn't provide a changed directory, treat as a new ontology by
   setting changed_directory.

  Args:
    filter_text: text used by the user to filter on types.
    original_directory: the original directory with ontology yaml files.
    changed_directory: the changed directory with ontology yaml files.
    interactive: flag to run validator in interactive mode or presubmit mode.
    require_type_guids: whether type guids are required to be present. This is
      needed to bypass write permission issues on the ontology validator GitHub
      Action.

  Raises:
    Exception: The Ontology is not valid.
  """
  if not changed_directory:
    changed_directory = original_directory
    original_directory = None

  modified_base = RecursiveDirWalk(original_directory)
  modified_client = RecursiveDirWalk(changed_directory)

  if interactive:
    presubmit_validate_types_lib.RunInteractive(
        filter_text, modified_base, modified_client, require_type_guids
    )
  else:
    findings = presubmit_validate_types_lib.RunPresubmit(
        [], modified_base, modified_client, require_type_guids
    )
    presubmit_validate_types_lib.PrintFindings(findings, '')
    # TODO(charbelk): add diff files in the presubmit in modified base
    findings_class = findings_lib.Findings()
    findings_class.AddFindings(findings)
    if not findings_class.IsValid():
      # pylint: disable=broad-exception-raised
      raise Exception('The Ontology is no longer valid.')


def RecursiveDirWalk(directory):
  """Walks recursively a directory and returns a list of PathParts.

  Args:
    directory: a directory with the ontology yaml files.

  Returns:
    path_parts: a list of PathParts.
  """
  if not directory:
    return []

  path_parts = []
  for dir_name, _, files in os.walk(directory, followlinks=False):
    tmp_relative_path = os.path.relpath(dir_name, directory)
    for yaml_file in files:
      if '.yaml' not in yaml_file:
        continue
      if tmp_relative_path != os.curdir:
        relative_path_yaml = os.path.join(tmp_relative_path, yaml_file)
      else:
        relative_path_yaml = yaml_file
      path_parts.append(
          base_lib.PathParts(root=directory, relative_path=relative_path_yaml)
      )

  return path_parts
