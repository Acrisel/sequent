from .VERSION import __version__
from .main import Sequent
from .sequent_types import SequentError, RunMode, StepReplay, StepStatus
from .utils import or_

STP_ACTIVE = StepStatus.active
STP_SUCCESS = StepStatus.success
STP_FAILURE = StepStatus.failure
STP_COMPLETE = StepStatus.complete

STP_SKIP = StepReplay.skip
STP_RERUN = StepReplay.rerun

SEQ_RESTART = RunMode.restart
SEQ_RECOVER = RunMode.recover
SEQ_REPLAY = RunMode.replay
SEQ_CONTINUE = RunMode.continue_
