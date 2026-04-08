# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Code Review Env Environment.

The code_review_env environment is a simple test environment that echoes back messages.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


#  ACTION (Agent response)
class CodeReviewAction(Action):
    response: str = Field(..., description="Agent's code review response")


#  OBSERVATION (What agent sees)
class CodeReviewObservation(Observation):
    code: str = Field(..., description="Code snippet to review")
    task: str = Field(..., description="Task description")


