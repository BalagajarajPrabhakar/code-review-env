# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Code Review Env Environment.
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
    reward: float = Field(default=0.0, description="Reward for the current step")
    done: bool = Field(default=False, description="Whether the episode is complete")
    task_name: str = Field(default="", description="Name of the current task")
    metadata: dict = Field(default_factory=dict, description="Extra metadata")
