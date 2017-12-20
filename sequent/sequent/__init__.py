from .VERSION import __version__
from .main import Sequent
from .sequent_types import SequentError, RunMode, StepReplay, StepStatus
from .utils import or_

ACTIVE = StepStatus.active
SUCCESS = StepStatus.success
FAILURE = StepStatus.failure
COMPLETE = StepStatus.complete

SKIP = StepReplay.skip
RERUN = StepReplay.rerun

RESTART = RunMode.restart
RECOVER = RunMode.recover
REPLAY = RunMode.replay
CONTINUE = RunMode.continue_
