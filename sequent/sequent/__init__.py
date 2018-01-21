__version__ = '3.1.4'

from .main import Sequent
from .sequent_types import SequentError, RunMode, StepReplay, StepStatus
from .utils import or_

STEP_READY = StepStatus.ready  # step is ready
STEP_ACTIVE = StepStatus.active  # step is active
STEP_SUCCESS = StepStatus.success  # step succeeded
STEP_FAILURE = StepStatus.failure  # step failed
STEP_COMPLETE = StepStatus.complete  # step complete with success or failure

STEP_SKIP = StepReplay.skip  # skip step if previously succeeded
STEP_RERUN = StepReplay.rerun  # reruns step regardless if previously succeeded

RUN_RESTART = RunMode.restart  # run flow from start
RUN_RECOVER = RunMode.recover  # reruns failed steps

# Note: internal use only
RUN_CONTINUE = RunMode.continue_  # continue from where it left in previous loop
