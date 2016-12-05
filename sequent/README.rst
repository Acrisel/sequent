=======
Sequent
=======

--------
Overview
--------

    *Sequent* provides programmer with interface to create flow.  *Sequent* is useful when there are multiple batch processes that should link together in processing flow.
    
    For example, programs A1, A2 extract data from database, program B process the extracted files, and programs C1 and C2 transmit process information to remote client.
    
    *Sequent* can be used to create the flow where A1, A2 would run concurrently, then program B would run.  When B is successful, programs C1 and C2 would run.
    
    *Sequent* uses *Eventor* as its underline infrastructure.  With that, it gains *Eventor*'s recovery capabilities.  When running in recovery, successful steps can be skipped.
    
    Considering the above example, this can be useful when C2 transmission program fails.  Recovery run would only execute it with out redoing potentially expensive work that was already completed (A1, A2, B, and C1)
    
    It would be easier to show an example. In this example, *Step s2* would run after *Step s1* would loop twice. When they are done, *Step s3* will run.  This flow would be repeat twice.

Simple Example
==============
    
    .. code-block:: python
        :number-lines:
        
        import sequent as seq
        import logging
        import time
        
        logger=logging.getLogger(__name__)
        
        def prog(progname, success=True):
            logger.info("doing what %s is doing" % progname)
            time.sleep(2) # mimic activity
            if not success:
                raise Exception("%s failed" % progname)
            return progname

        myflow=seq.Sequent(logging_level=logging.INFO)

        s0=myflow.add_step('s0', loop=[1,2])
        s00=s0.add_step('s00', loop=[1,2,])
        
        s1=s00.add_step('s1', func=prog, kwargs={'progname': 'prog1'}) 
        s2=s00.add_step('s2', func=prog, kwargs={'progname': 'prog2'}, require=( (s1, seq.StepStatus.success), )) 
        
        s3=s0.add_step('s3', func=prog, kwargs={'progname': 'prog3'}, require=( (s00, seq.StepStatus.success), )) 

        myflow()   
     
Example Output
==============

    The above example with provide the following log output.  Note more detailed logging activities was stripped off.  Only actual shows actual program activity is shown.
    
    .. code-block:: python
        :number-lines:

        [ 2016-12-05 11:56:21,363 ][ INFO ][ Eventor store file: /private/var/acrisel/sand/sequent/sequent/sequent/example/runly00.run.db ]
        .
        .
        [ 2016-12-05 11:56:21,624 ][ INFO ][ doing what prog1 is doing ]
        .
        .
        [ 2016-12-05 11:56:24,804 ][ INFO ][ doing what prog2 is doing ]
        .
        .
        [ 2016-12-05 11:56:28,032 ][ INFO ][ doing what prog1 is doing ]
        .
        .
        [ 2016-12-05 11:56:31,228 ][ INFO ][ doing what prog2 is doing ]
        .
        .
        [ 2016-12-05 11:56:34,540 ][ INFO ][ doing what prog3 is doing ]
        .
        .
        [ 2016-12-05 11:56:37,845 ][ INFO ][ doing what prog1 is doing ]
        .
        .
        [ 2016-12-05 11:56:41,036 ][ INFO ][ doing what prog2 is doing ]
        .
        .
        [ 2016-12-05 11:56:44,233 ][ INFO ][ doing what prog1 is doing ]
        .
        .
        [ 2016-12-05 11:56:47,425 ][ INFO ][ doing what prog2 is doing ]
        .
        .
        [ 2016-12-05 11:56:50,727 ][ INFO ][ doing what prog3 is doing ]
        .
        .
        [ 2016-12-05 11:56:53,928 ][ INFO ][ Processing finished: True ]

Code Highlights
===============

    For simplicity, code definition of prog (line 7) serves as reusable activity for all the steps in this example.
    
    A *Sequent* object is defined (line 14) to host myflow.
    
    An hierarchically defines S0 and S00 as *container* steps.  s0 (line )
    
    *add_event* (e.g., line 12) adds an event named **run_step1** to the respective eventor object.
    
    *add_step* (e.g., line 16) adds step **s1** which when triggered would run predefined function **prog** with key words parameters **progname='prog1'**.
    Additionally, when step would end, if successful, it would trigger event **evs2**
    
    *add_assoc* (e.g., line 22) links event **evs1** and step **s1**.
    
    *trigger_event* (line 26) marks event **evs1**; when triggers, event is associated with sequence.  This would allow multiple invocation.
    
    *ev()* (line 27) invoke eventor process that would looks for triggers and tasks to act upon.  It ends when there is nothing to do.
 
-----------------
Eventor Interface
-----------------

Eventor 
=======

Envtor Class Initiator
----------------------

    .. code::
        
        Eventor(name='', store='', run_mode=RunMode.restart, recovery_run=None, logging_level=logging.INFO, config={})

Args
````

    name: string id for Eventor object initiated
    
    store: path to file that would store runnable (sqlite) information; if ':memory:' is used, in-memory temporary 
        storage will be created.  If not provided, calling module path and name will be used 
        with db extension instead of py
    
    run_mode: can be either *RunMode.restart* (default) or *RunMode.recover*; in restart, new instance or the run 
        will be created. In recovery, 
              
    recovery_run: if *RunMode.recover* is used, *recovery_run* will indicate specific instance of previously recovery 
        run that would be executed.If not provided, latest run would be used.
          
    config: keyword dictionary of default configurations.  Available keywords and their default values:
    
        +---------------------+------------+--------------------------------------------------+
        | Name                | Default    | Description                                      |
        |                     | Value      |                                                  |
        +=====================+============+==================================================+
        | workdir             | /tmp       | place to create necessry artifacts (not in use)  |
        +---------------------+------------+--------------------------------------------------+
        | logdir              | /tmp       | place to create debug and error log files        |
        +---------------------+------------+--------------------------------------------------+
        | task_construct      | mp.Process | method to use for execution of steps             |
        +---------------------+------------+--------------------------------------------------+
        | max_concurrent      | 1          | maximum concurrent processing, if value <1, no   |
        |                     |            | limit will be pose                               |
        +---------------------+------------+--------------------------------------------------+
        | stop_on_exception   | True       | if an exception occurs in a step, stop           |
        |                     |            | all processes.  If True, new processes will not  |
        |                     |            | start.  But running processes will be permitted  |
        |                     |            | to finish                                        |
        +---------------------+------------+--------------------------------------------------+
        | sleep_between_loops | 1          | seconds to sleep between iteration of checking   |
        |                     |            | triggers and tasks                               |
        +---------------------+------------+--------------------------------------------------+
          
Envtor add_event method
-----------------------

    .. code::
        
        add_event(name, expr=None)

Args
````

    *name*: string unique id for event 
    
    *expr*: logical expression 'sqlalchemy' style to automatically raise this expresion.
        syntax: 
        
        .. code ::
            
            expr : (expr, expr, ...)
                 | or_(expr, expr, ...) 
                 | event
                 
        - if expression is of the first style, logical *and* will apply.
        - the second expression will apply logical *or*.
        - the basic atom in expression is *even* which is the product of add_event.
        
Returns
```````

    Event object to use in other add_event expressions, add_assoc methods, or with add_step triggers.
    
Envtor add_step method
-----------------------

    .. code::
        
        add_step(name, func, args=(), kwargs={}, triggers={}, recovery={}, config={})

Args
````

    *name*: string unique id for step 
    
    *func*: callable object that would be call at time if step execution
    
    *args*: tuple of values that will be passed to *func* at calling
    
    *kwargs*: keywords arguments that will be pust to *func* at calling
    
    *triggers*: mapping of step statuses to set of events to be triggered as in the following table:
    
        +--------------------+-------------------------------------------+
        | status             | description                               |
        +====================+===========================================+
        | StepState.ready    | set when task is ready to run (triggered) |
        +--------------------+-------------------------------------------+
        | StepState.active   | set when task is running                  |
        +--------------------+-------------------------------------------+
        | StepState.success  | set when task is successful               |
        +--------------------+-------------------------------------------+
        | StepState.failure  | set when task fails                       |
        +--------------------+-------------------------------------------+
        | StepState.complete | stands for success or failure of task     |
        +--------------------+-------------------------------------------+
        
        
    *recovery*: mapping of state status to how step should be handled in recovery:
    
        +---------------------+------------------+------------------------------------------------------+
        | status              | default          | description                                          |
        +=====================+==================+======================================================+
        | TaskStatus.ready    | StepReplay.rerun | if in recovery and previous status is ready, rerun   |
        +---------------------+------------------+------------------------------------------------------+
        | TaskStatus.active   | StepReplay.rerun | if in recovery and previous status is active, rerun  |
        +---------------------+------------------+------------------------------------------------------+
        | TaskStatus.failure  | StepReplay.rerun | if in recovery and previous status is failure, rerun |
        +---------------------+------------------+------------------------------------------------------+
        | TaskStatus.success  | StepReplay.skip  | if in recovery and previous status is success, skip  |
        +---------------------+------------------+------------------------------------------------------+
    
    *config*: keywords mapping overrides for step configuration.
    
        +-------------------+------------------+---------------------------------------+
        | name              | default          | description                           |
        +===================+==================+=======================================+
        | stop_on_exception | True             | stop flow if step ends with Exception | 
        +-------------------+------------------+---------------------------------------+
    
Returns
```````

    Step object to use in add_assoc method.
    
Envtor add_assoc method
-----------------------

    .. code::
        
        add_assoc(event, *assocs)

Args
````

    *event*: event objects as provided by add_event.
    
    *assocs*: list of associations objects.  List is composed from either events (as returned by add_event) or steps (as returned by add_step)
    
Returns
```````

    N/A
    
Envtor trigger_event method
---------------------------

    .. code::
        
        trigger_event(event, sequence=None)

Args
````

    *event*: event objects as provided by add_event.
    
    *sequence*: unique association of triggered event.  Event can be triggered only once per sequence.  All derivative triggers will carry the same sequence.
    
Returns
```````

    N/A
    
----------------------
Additional Information
----------------------

    Eventor github project (https://github.com/Acrisel/sequent) has additional examples with more complicated flows.
    
    
    



 