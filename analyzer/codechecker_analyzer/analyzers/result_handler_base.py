# -------------------------------------------------------------------------
#
#  Part of the CodeChecker project, under the Apache License v2.0 with
#  LLVM Exceptions. See LICENSE for license information.
#  SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
#
# -------------------------------------------------------------------------
"""
Result handlers to manage the output of the static analyzers.
"""


from abc import ABCMeta
import hashlib
import os

from codechecker_common.logger import get_logger

LOG = get_logger('analyzer')


class ResultHandler(object, metaclass=ABCMeta):
    """
    Handle and store the results at runtime for the analyzer:
    stdout, stderr, temporarily generated files.
    Do result postprocessing if required.

    For each buildaction there is one result handler.
    The result handler can handle multiple results if there
    are more than one analyzed source file in one buildaction.

    handle_results() handles the results and returns report statistics.

    For each build action
    - postprocess_result and handle_results can be called multiple times
      for the source files in one buildaction they will be analyzed separately
      with the same build options.

    Method call order should be:
    postprocess_result()
    handle_results()
    """
    # Handle the output stdout, or plist or both for an analyzer.

    def __init__(self, action, workspace, report_hash_type=None):
        """
        Put the temporary files for the workspace.
        """
        self.__workspace = workspace

        self.analyzer_cmd = []
        self.analyzer_stdout = ''
        self.analyzer_stderr = ''
        self.severity_map = {}
        self.skiplist_handler = None
        self.analyzed_source_file = None
        self.analyzer_returncode = 1
        self.__buildaction = action

        self.__result_file = None
        self.__fixit_file = None

        # Report hash type can influence the post processing
        # of the results by rewriting the generated
        # report id (hash) values.
        self.report_hash_type = report_hash_type

    @property
    def buildaction(self):
        """
        """
        return self.__buildaction

    @property
    def workspace(self):
        """
        Workspace where the analysis results and temporarily generated files
        should go.
        """
        return self.__workspace

    @property
    def analyzer_action_str(self):
        """
        Generate a string which is unique to the analyzed build action. The
        returned string contains information of the analyzed file, the analyzer
        and the build command.
        """
        analyzed_file_name = os.path.basename(self.analyzed_source_file)

        source_file = os.path.normpath(
            os.path.join(self.buildaction.directory,
                         self.analyzed_source_file))

        build_info = source_file + '_' + \
            self.buildaction.original_command

        return analyzed_file_name + '_' + \
            str(self.buildaction.analyzer_type) + '_' + \
            hashlib.md5(build_info.encode(errors='ignore')).hexdigest()

    @property
    def analyzer_result_file(self):
        """
        Generate a result filename where the analyzer should put the results.
        Result file should be removed by the result handler eventually.
        """
        if not self.__result_file:
            self.__result_file = os.path.join(
                self.__workspace,
                self.analyzer_action_str + '.plist')

        return self.__result_file

    @property
    def fixit_file(self):
        """
        Generate a filename where the analyzer should put the fixit results.
        This is a .yaml file which contains the replacements which can be
        applied by clang-apply-replacements tool.
        """
        if not self.__fixit_file:
            self.__fixit_file = os.path.join(
                self.__workspace,
                'fixit',
                self.analyzer_action_str + '.yaml')

        return self.__fixit_file

    def clean_results(self):
        """
        Should be called after the postprocessing and result handling is done.
        """
        if self.__result_file:
            try:
                os.remove(self.__result_file)
            except OSError as oserr:
                # There might be no result file if analysis failed.
                LOG.debug(oserr)

    def postprocess_result(self):
        """
        Postprocess result if needed.
        Should be called after the analyses finished.
        """
        pass

    def handle_results(self, client):
        """
        Handle the results and return report statistics.
        """
        pass
