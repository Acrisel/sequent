=======
Sequent
=======

------------------------------------------------------------
Programming interface to use in programs to create task flow
------------------------------------------------------------

.. contents:: Table of Contents
   :depth: 1

Overview
========

    *Sequent* provides programmer with interface to create flow.  *Sequent* is useful when there are multiple batch processes that should link together in processing flow.
    
    For example, programs A1, A2 extract data from database, program B process the extracted files, and programs C1 and C2 transmit process information to remote client.
    
    *Sequent* can be used to create the flow where A1, A2 would run concurrently, then program B would run.  When B is successful, programs C1 and C2 would run.
    
    *Sequent* uses *Eventor* (https://github.com/Acrisel/eventor) as its underline infrastructure. With that, it gains *Eventor*'s recovery capabilities.  When running in recovery, successful steps can be skipped.
    
    Considering the above example, this can be useful when C2 transmission program fails. Recovery run would only execute it with out redoing potentially expensive work that was already completed (A1, A2, B, and C1)
    
    It would be easier to show an example. In this example, *Step s2* would run after *Step s1* would loop twice. When they are done, *Step s3* will run.  This flow would be repeat twice.

Simple Example
--------------
    
    .. code-block:: python
        :number-lines:
        
        import sequent as seq
        import logging

        def prog(progname, success=True):
            logger = logging.getLogger(os.getenv("SEQUENT_LOGGER_NAME"))
            logger.info("doing what {} is doing".format(progname))
            if not success:
                raise Exception("{} failed".format(progname))
            return progname

        myflow = seq.Sequent(config={'sleep_between_loops': 0.05, 
                                     'LOGGING': {'logging_level':logging.DEBUG}})

        s1 = myflow.add_step('s1', repeats=[1,2])

        s11 = s1.add_step('s11', repeats=[1,2,])

        s111 = s11.add_step('s111', func=prog, kwargs={'progname': 'prog1'}) 
        s112 = s11.add_step('s112', func=prog, kwargs={'progname': 'prog2'}, 
                          requires=( (s111, seq.STEP_SUCCESS), )) 

        s12 = s1.add_step('s12', func=prog, kwargs={'progname': 'prog3'}, 
                        require=s( (s11, seq.STEP_SUCCESS), )) 

        s2 = myflow.add_step('s2', func=prog, kwargs={'progname': 'prog4'}, 
                           requires=((s1, seq.STEP_SUCCESS),)) 

        myflow.run() 
           
Example Output
--------------

    The above example with provide the following log output. Note more detailed logging activities was stripped off.  Only actual shows actual program activity is shown.
    
    .. code-block:: python
        :number-lines:

        [ 2016-12-07 11:14:29,761 ][ INFO ][ Eventor store file: /sequent/example/runly00.run.db ]
        ...
        [ 2016-12-07 11:14:29,962 ][ INFO ][ doing what prog1 is doing ]
        ...
        [ 2016-12-07 11:14:30,124 ][ INFO ][ doing what prog2 is doing ]
        ...
        [ 2016-12-07 11:14:30,358 ][ INFO ][ doing what prog1 is doing ]
        ...
        [ 2016-12-07 11:14:30,587 ][ INFO ][ doing what prog2 is doing ]
        ...
        [ 2016-12-07 11:14:30,908 ][ INFO ][ doing what prog3 is doing ]
        ...
        [ 2016-12-07 11:14:31,234 ][ INFO ][ doing what prog1 is doing ]
        ...
        [ 2016-12-07 11:14:31,407 ][ INFO ][ doing what prog2 is doing ]
        ...
        [ 2016-12-07 11:14:31,657 ][ INFO ][ doing what prog1 is doing ]
        ...
        [ 2016-12-07 11:14:31,894 ][ INFO ][ doing what prog2 is doing ]
        ...
        [ 2016-12-07 11:14:32,240 ][ INFO ][ doing what prog3 is doing ]
        ...
        [ 2016-12-07 11:14:32,565 ][ INFO ][ doing what prog4 is doing ]
        ...
        [ 2016-12-07 11:14:32,713 ][ INFO ][ Processing finished with: success ]

Code Highlights
---------------

    Flow diagram:
    
    .. code-block:: python
    
         
        +--S1----------------------+
        |                          |
        | +--S11----------+        |
        | |               |        |
        | | S111  -> S112 | -> S12 | -> S2
        | +---------------+        |
        +--------------------------+

    For simplicity, code definition of prog (line 6) serves as reusable activity for all the steps in this example.
    
    A *Sequent* object is defined (line 12) to host myflow. By default, Sequent's Eventor loops on events and steps.  By defaults it sleeps one second between loops. Here '*sleep_between_loops*' changes this setting to 0.05 seconds. 
    
    myflow contains two steps, *s1* and *s2*. *s1* is a container step that would repeat twice (defined on line 15). *s2* is a processing step (defined on line 26).
    
    *s1* contains two steps. *s11* (line 17) is *container* step and *s12* is a processing step.  
    
    *s11* contains two processing steps *s111* and *s112* (lines 19-20).  
    
    Finally, on line 29 the flow is executed using *myflow()*.
    
    *logger* is set with in step program (line 5) to direct step logging into its dedicated log.
 
Sequent Interface
=================

Sequent Class Initiator
-----------------------

    Sequent signature in its most simplistic format:
    
    .. code-block:: python
        
        Sequent(name='', store='', run_mode=SEQ.SEQUENT_RESTART, recovery_run=None, config={}, config_tag='')

Description
```````````

    Sequent, when instantiated, provides interface to build program flow. When called upon, *Sequent* steps are translated to *Eventor* steps and *Step*'s *requires* are translated to *Eventor*'s *Events* and *Steps'* *triggers*.
    
    Sequent instantiation arguments are the same as *Eventor*'s.  

Args
````

    name: string id for Sequent object initiated.
    
    store: path to file that would store runnable (sqlite) information; if ':memory:' is used, in-memory temporary 
        storage will be created.  If not provided, calling module path and name will be used 
        with db extension instead of 'py'.
    
    run_mode: can be either *RUN_RESTART* (default) or *RUN_RECOVER*; in restart, new instance or the run 
        will be created. In recovery, 
              
    recovery_run: if *RUN_RECOVER* is used, *recovery_run* will indicate specific instance of previously recovery 
        run that would be executed.If not provided, latest run would be used.
          
    config: keyword dictionary of default configurations. Available keywords and their default values:
    
        +---------------------+------------------+--------------------------------------------------+
        | Name                | Default          | Description                                      |
        |                     | Value            |                                                  |
        +=====================+==================+==================================================+
        | workdir             | /tmp             | place to create necessry artifacts (not in use)  |
        +---------------------+------------------+--------------------------------------------------+
        | logdir              | /var/log/eventor | place to create debug and error log files        |
        +---------------------+------------------+--------------------------------------------------+
        | task_construct      | 'process'        | method to use for execution of steps             |
        +---------------------+------------------+--------------------------------------------------+
        | max_concurrent      | 1                | maximum concurrent processing, if value <1, no   |
        |                     |                  | limit will be pose                               |
        +---------------------+------------------+--------------------------------------------------+
        | stop_on_exception   | True             | if an exception occurs in a step, stop           |
        |                     |                  | all processes. If True, new processes will not   |
        |                     |                  | start. But running processes will be permitted   |
        |                     |                  | to finish                                        |
        +---------------------+------------------+--------------------------------------------------+
        | sleep_between_loops | 1                | seconds to sleep between iteration of checking   |
        |                     |                  | triggers and tasks                               |
        +---------------------+------------------+--------------------------------------------------+
        
    config_tag: key with in config where Sequent configuration starts.
          
Sequent add_event method
------------------------

    .. code-block:: python
        
        add_event(require=None)

Args
````

    *requires*: logical expression 'sqlalchemy' style to automatically raise this expression.
        syntax: 
        
        .. code-block:: python
            
            requires : (requires, requires, ...)
                     | or_(requires, requires, ...) 
                     | event
                 
        - if expression is of the first style, logical *and* will apply.
        - the second expression will apply logical *or*.
        - the basic atom in expression is *even* which is the product of add_event.
        
Returns
```````

    Event object to use are require in *add_step*.
    
Sequent add_step method
-----------------------

    .. code-block:: python
        
        add_step(name, func, args=(), kwargs={}, hosts=[], requires={}, delay=0, acquires=[], releases=None, recovery={}, config={})

Args
````

    *name*: string unique id for step 
    
    *func*: callable object that would be call at time if step execution
    
    *args*: tuple of values that will be passed to *func* at calling
    
    *kwargs*: keywords arguments that will be passed to *func* at calling
    
    *hosts*: list of hosts step should run on. If not provided, *localhost* will be used.
        if 
    
    *requires*: mapping of step statuses such that when set of events, added step will be launched:
    
        +---------------+-------------------------------------------+
        | status        | description                               |
        +===============+===========================================+
        | STEP_READY    | set when task is ready to run (triggered) |
        +---------------+-------------------------------------------+
        | STEP_ACTIVE   | set when task is running                  |
        +---------------+-------------------------------------------+
        | STEP_SUCCESS  | set when task is successful               |
        +---------------+-------------------------------------------+
        | STEP_FAILURE  | set when task fails                       |
        +---------------+-------------------------------------------+
        | STEP_COMPLETE | stands for success or failure of task     |
        +---------------+-------------------------------------------+
        
    *delay*: seconds to wait before executing step once is requires are available.  Actual execution 
        may be delayed further if resources needs to be acquired.
    
    *acquires*: list of tuples of resource pool and amount of resources to acquire before starting. 
    
    *releases*: list of tuples of resources pool and amount of resources to release once completed.
        If None, defaults to *acquires*.  If set to empty list, none of the acquired resources would 
        be released.
            
    *recovery*: mapping of state status to how step should be handled in recovery:
    
        +--------------+-----------+------------------------------------------------------+
        | status       | default   | description                                          |
        +==============+===========+======================================================+
        | STEP_READY   | STP_RERUN | if in recovery and previous status is ready, rerun   |
        +--------------+-----------+------------------------------------------------------+
        | STEP_ACTIVE  | STP_RERUN | if in recovery and previous status is active, rerun  |
        +--------------+-----------+------------------------------------------------------+
        | STEP_FAILURE | STP_RERUN | if in recovery and previous status is failure, rerun |
        +--------------+-----------+------------------------------------------------------+
        | STEP_SUCCESS | STP_SKIP  | if in recovery and previous status is success, skip  |
        +--------------+-----------+------------------------------------------------------+
    
    *config*: keywords mapping overrides for step configuration.
    
        +-------------------+---------------+---------------------------------------+
        | name              | default       | description                           |
        +===================+===============+=======================================+
        | stop_on_exception | True          | stop flow if step ends with Exception | 
        +-------------------+---------------+---------------------------------------+
    
Returns
```````

    Step object to use in add_assoc method.

Sequent run method
------------------

    .. code-block:: python
    
        run(max_loops=-1)
        
when calling *run* method, information is built and loops evaluating events and task starts are executed.  
In each loop events are raised and tasks are performed.  max_loops parameters allows control of how many
loops to execute.

In simple example, **myflow.run()** engage Sequent's run() method.
        
Args
````

    *max_loops*: max_loops: number of loops to run.  If positive, limits number of loops.
                 defaults to negative, which would run loops until there are no events to raise and
                 no task to run. 
                 
Returns
```````

    If there was a failure that was not followed by event triggered, result will be False.

Distributed Operation 
=====================

*Sequent* can operate Steps on distributed environment. A step can be associated with hosts using *hosts* argument in *add_step*. *Sequent* uses SSH to submit steps to remote host. This means that cluster needs to be configured with SSH keys. To set up the environment for *Sequent* distributed operation:

1. Host from which *Sequent* program would be initiated, should be able to SSH to participating hosts without only using keys.
#. SSH authorized_keys on each target host should has proper *command* to initiate the right operation environment.  This may include activating the correct virtualenv.
#. Optionally, set SSH backdoor to originated host. In the future *Sequent* may use this backdoor, as callback.
#. Software needs to be uniformly installed on all participating machines.
#. *Sequent* must be initiated with database configuration that is accessible from all participating hosts.  *Sequent* and its remote agents would use that database to share  operation information. The database user needs to have permissions to create schema (if the associated schema is not created.) It also needs to have create table permissions.
#. Anything passed to Sequent, predominately with *add_step*, needs to be importable. For example in simple example:

    .. code-block:: python
    
        import example_progs as example
        
        s111 = s11.add_step('s111', func=example.prog, kwargs={'progname': 'prog1'})


Recovery
========

    Recovery allows rerun of a program in a way that it will skip successful steps.  To use recovery, store mast be physical (cannot use in-memory).  
    
    According to step recovery setup, when in recovery, step may be skipped or rerun.  By default, only success statuses are skipped.
    
    Here is an example for recovery program and run.
    
Recovery Example
----------------

    .. code-block:: python
        :number-lines:
            
        import sequent as sqnt
        import logging

        appname = os.path.basename(__file__)
        logger = logging.getLogger(appname)

        def prog(flow, progname, step_to_fail=None, iteration_to_fail=''):
            logger = logging.getLogger(os.getenv("SEQUENT_LOGGER_NAME"))
            step_name = flow.get_step_name() 
            step_sequence = flow.get_step_sequence()
            logger.info("doing what {} is doing (}/{})".format(progname, step_name, step_sequence))
            if step_to_fail == step_name and step_sequence== iteration_to_fail:
                raise Exception("{} failed ({}/{})".format(progname, step_name, step_sequence))
            return progname

        def build_flow(run_mode = sqnt.RUN_RESTART, run_id=None, step_to_fail=None, iteration_to_fail=''):
            myflow = sqnt.Sequent(name=appname, run_mode=run_mode, run_id=run_id, config={'sleep_between_loops': 0.05,}, )

            s1 = myflow.add_step('s1', repeats=[1,2])
    
            s11 = s1.add_step('s11', repeats=[1,2,])
    
            s111 = s11.add_step('s111', func=prog, kwargs={'flow': myflow, 'progname': 'prog1', 
                                                         'step_to_fail':step_to_fail, 
                                                         'iteration_to_fail':iteration_to_fail,}) 
            s112 = s11.add_step('s112', func=prog, kwargs={'flow': myflow, 'progname': 'prog2', 
                                                         'step_to_fail':step_to_fail, 
                                                         'iteration_to_fail':iteration_to_fail,}, 
                              requires=((s111, sqnt.STEP_SUCEESS),)) 
    
            s12 = s1.add_step('s12', func=prog, kwargs={'flow': myflow, 'progname': 'prog3', 
                                                      'step_to_fail':step_to_fail, 
                                                      'iteration_to_fail':iteration_to_fail,}, 
                            requires=((s11, sqnt.STEP_SUCEESS),)) 
    
            s2 = myflow.add_step('s2', func=prog, kwargs={'flow': myflow, 'progname': 'prog4', 
                                                        'step_to_fail':step_to_fail, 
                                                        'iteration_to_fail':iteration_to_fail,}, 
                               requires=((s1, sqnt.STEP_SUCEESS),)) 
            return myflow

        # creating flow simulating failure
        myflow = build_flow(step_to_fail='s1_s11_s111', iteration_to_fail='1.2.2')
        myflow.run()
        
        run_id = myflow.run_id

        # creating recovery flow
        myflow = build_flow(run_mode=RUN_RECOVER, run_id=run_id)
        myflow.run()
    
Example Output
--------------

    .. code-block:: python
        :number-lines:
        
        [ 2016-12-07 14:49:24,437 ][ INFO ][ Eventor store file: /sequent/example/runly04.run.db ]
        ...
        [ 2016-12-07 14:49:24,645 ][ INFO ][ doing what prog1 is doing (s1_s11_s111/1.1.1) ]
        ...
        [ 2016-12-07 14:49:24,805 ][ INFO ][ doing what prog2 is doing (s1_s11_s112/1.1.1) ]
        ...
        [ 2016-12-07 14:49:25,047 ][ INFO ][ doing what prog1 is doing (s1_s11_s111/1.1.2) ]
        ...
        [ 2016-12-07 14:49:25,272 ][ INFO ][ doing what prog2 is doing (s1_s11_s112/1.1.2) ]
        ...
        [ 2016-12-07 14:49:25,587 ][ INFO ][ doing what prog3 is doing (s1_s12/1.1) ]
        ...
        [ 2016-12-07 14:49:25,909 ][ INFO ][ doing what prog1 is doing (s1_s11_s111/1.2.1) ]
        ...
        [ 2016-12-07 14:49:26,073 ][ INFO ][ doing what prog2 is doing (s1_s11_s112/1.2.1) ]
        ...
        [ 2016-12-07 14:49:26,321 ][ INFO ][ doing what prog1 is doing (s1_s11_s111/1.2.2) ]
        [ 2016-12-07 14:49:26,323 ][ INFO ][ [ Step s1_s11_s111/1.2.2 ] Completed, status: TaskStatus.failure ]
        [ 2016-12-07 14:49:26,397 ][ ERROR ][ Exception in run_action: 
            <Task(id='15', step_id='s1_s11_s111', sequence='1.2.2', recovery='0', pid='10276', status='TaskStatus.failure', created='2016-12-07 20:49:26.300030', updated='2016-12-07 20:49:26.311884')> ]
        [ 2016-12-07 14:49:26,397 ][ ERROR ][ Exception('prog1 failed (s1_s11_s111/1.2.2)',) ]
        [ 2016-12-07 14:49:26,397 ][ ERROR ][ File "/eventor/eventor/main.py", line 63, in task_wrapper
                    result=step(seq_path=task.sequence)
        File "/eventor/eventor/step.py", line 82, in __call__
                    result=func(*func_args, **func_kwargs)
        File "/sequent/example/runly04.py", line 34, in prog
                    raise Exception("%s failed (%s/%s)" % (progname, step_name, step_sequence)) ]
        [ 2016-12-07 14:49:26,397 ][ INFO ][ Stopping running processes ]
        [ 2016-12-07 14:49:26,401 ][ INFO ][ Processing finished with: failure ]
        [ 2016-12-07 14:49:26,404 ][ INFO ][ Eventor store file: /sequent/example/runly04.run.db ]
        ...
        [ 2016-12-07 14:49:27,921 ][ INFO ][ doing what prog1 is doing (s1_s11_s111/1.2.2) ]
        ...
        [ 2016-12-07 14:49:28,159 ][ INFO ][ doing what prog2 is doing (s1_s11_s112/1.2.2) ]
        ...
        [ 2016-12-07 14:49:28,494 ][ INFO ][ doing what prog3 is doing (s1_s12/1.2) ]
        ...
        [ 2016-12-07 14:49:28,844 ][ INFO ][ doing what prog4 is doing (s2/1) ]
        [ 2016-12-07 14:49:28,845 ][ INFO ][ [ Step s2/1 ] Completed, status: TaskStatus.success ]
        [ 2016-12-07 14:49:29,002 ][ INFO ][ Processing finished with: success ]

Example Highlights
------------------
    
    The function *build_flow* (code line 14) build a Sequent flow similarly to simple example above.  Since no specific store is provided in Sequent instantiation, a default runner store is assigned (code line 15). In this build, steps will use default recovery directives whereby successful steps are skipped.  
    
    The first build and run is done in lines 42-43. In this run, a parameter is passed to cause step *s111* in its fourth iteration to fail.  As a result, flow fails.  Output lines 1-29 is associated with the first run.  
    
    The second build and run is then initiated.  In this run, parameter is set to a value that would pass step *s111* and run mode is set to recovery (code lines 45-46). Eventor skips successful steps and start executing from failed steps onwards. Output lines 30-40 reflects successful second run.
    
    Note that the second run required a **run_id** of the run that is reactivated. *run_id* is fetched from its corresponding attribute in *Sequent* Objects.
    
    For prog to know when to default, it uses the following methods flow.get_step_name() and flow.get_step_sequence() (lines 7-8). Those Sequent methods allow access to Eventor step attributes. Another way
    to access these attributes is via os.environ:
    
    .. code-block:: python
    
         name = os.getenv('SEQUENT_STEP_NAME')
         sequence = os.getenv('SEQUENT_STEP_SEQUENCE')
         recovery = os.getenv('SEQUENT_STEP_RECOVERY')
         logger_name = os.getenv('SEQUENT_LOGGER_NAME')
         
Distributed Example
-------------------

Resources
=========

    *add_step* allows association of step with resources.  If acquires argument is provided, before step starts, *Eventor* 
    will attempt to reserve resources.  Step will be executed only when resources are secured.
    
    When *release* argument is provided, resources resources listed as its value will be released when step is done.  If 
    release is None, whatever resources stated by *acquires* would be released.  If the empty list is set as value, no 
    resource would be released.
    
    To use resources, program to use Resource and ResourcePool from acris.virtual_resource_pool.  Example for such definitions are below.
    
Example for resources definitions
---------------------------------

    .. code-block:: python
        :number-lines:
        
        import sequent as sqnt
        from acris import virtual_resource_pool as vrp

        class Resources1(vrp.Resource): pass
        class Resources2(vrp.Resource): pass
        
        rp1 = vrp.ResourcePool('RP1', resource_cls=Resources1, policy={'resource_limit': 2, }).load()                   
        rp2 = vrp.ResourcePool('RP2', resource_cls=Resources2, policy={'resource_limit': 2, }).load()
        
        myflow = sqnt.Sequent(config={'sleep_between_loops': 0.05,}, )
        s1 = myflow.add_step('s1', repeats=[1,2], acquires=[(rp1, 2), ])
    
Additional Information
======================

    Sequent github project (https://github.com/Acrisel/sequent) has additional examples with more complicated flows.
    
    
    



 