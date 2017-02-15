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
    
    *Sequent* uses *Eventor* (https://github.com/Acrisel/eventor) as its underline infrastructure.  With that, it gains *Eventor*'s recovery capabilities.  When running in recovery, successful steps can be skipped.
    
    Considering the above example, this can be useful when C2 transmission program fails.  Recovery run would only execute it with out redoing potentially expensive work that was already completed (A1, A2, B, and C1)
    
    It would be easier to show an example. In this example, *Step s2* would run after *Step s1* would loop twice. When they are done, *Step s3* will run.  This flow would be repeat twice.

Simple Example
--------------
    
    .. code-block:: python
        :number-lines:
        
        import sequent as seq
        import logging

        logger=logging.getLogger(__name__)

        def prog(progname, success=True):
            logger.info("doing what %s is doing" % progname)
            if not success:
                raise Exception("%s failed" % progname)
            return progname

        myflow=seq.Sequent(logging_level=logging.INFO, 
                           config={'sleep_between_loops': 0.05,})

        s1=myflow.add_step('s1', repeat=[1,2])

        s11=s1.add_step('s11', repeat=[1,2,])

        s111=s11.add_step('s111', func=prog, kwargs={'progname': 'prog1'}) 
        s112=s11.add_step('s112', func=prog, kwargs={'progname': 'prog2'}, 
                          requires=( (s111, seq.StepStatus.success), )) 

        s12=s1.add_step('s12', func=prog, kwargs={'progname': 'prog3'}, 
                        require=s( (s11, seq.StepStatus.success), )) 

        s2=myflow.add_step('s2', func=prog, kwargs={'progname': 'prog4'}, 
                           requires=( (s1, seq.StepStatus.success), )) 

        myflow.run() 
        myflow.close()
           
Example Output
--------------

    The above example with provide the following log output.  Note more detailed logging activities was stripped off.  Only actual shows actual program activity is shown.
    
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

    For simplicity, code definition of prog (line 6) serves as reusable activity for all the steps in this example.
    
    A *Sequent* object is defined (line 12) to host myflow.  By default, Sequent's Eventor loops on events and steps.  By defaults it sleeps one second between loops.  Here '*sleep_between_loops*' changes this setting to 0.05 seconds. 
    
    myflow contains two steps, *s1* and *s2*.  *s1* is a container step that would repeat twice (defined on line 15). *s2* is a processing step (defined on line 26).
    
    *s1* contains two steps. *s11* (line 17) is *container* step and *s12* is a processing step.  
    
    *s11* contains two processing steps *s111* and *s112* (lines 19-20).  
    
    Finally, on line 29 the flow is executed using *myflow()*.
 

Sequent Interface
=================

Sequent Class Initiator
-----------------------

    .. code::
        
        Sequent(name='', store='', run_mode=RunMode.restart, recovery_run=None, logging_level=logging.INFO, config={})

Description
```````````

    Sequent, when instantiated, provides interface to build program flow.  When called upon, *Sequent* steps are translated to *Eventor* steps and *Step*'s *requires* are translated to *Eventor*'s *Events* and *Steps'* *triggers*.
    
    Sequent instantiation arguments are the same as *Eventor*'s.  

Args
````

    name: string id for Sequent object initiated
    
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
          
Sequent add_event method
------------------------

    .. code::
        
        add_event(require=None)

Args
````

    *requires*: logical expression 'sqlalchemy' style to automatically raise this expresion.
        syntax: 
        
        .. code ::
            
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

    .. code::
        
        add_step(name, func, args=(), kwargs={}, requires={}, delay=0, acquires=[], releases=None, recovery={}, config={})

Args
````

    *name*: string unique id for step 
    
    *func*: callable object that would be call at time if step execution
    
    *args*: tuple of values that will be passed to *func* at calling
    
    *kwargs*: keywords arguments that will be pust to *func* at calling
    
    *requires*: mapping of step statuses such that when set of events, added step will be launched:
    
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
        
    *delay*: seconds to wait before executing step once ts requires are available.  Actual execution 
        may be delayed further if resources needs to be acquired.
    
    *acquires*: list of tuples of resource pool and amount of resources to acquire before starting. 
    
    *releases*: list of tuples of resources pool and amount of resources to release once completed.
        If None, defaults to *acquires*.  If set to empty list, none of the acquired resources would 
        be released.
            
    *recovery*: mapping of state status to how step should be handled in recovery:
    
        +-----------------------+------------------+------------------------------------------------------+
        | status                | default          | description                                          |
        +=======================+==================+======================================================+
        | StatusStatus.ready    | StepReplay.rerun | if in recovery and previous status is ready, rerun   |
        +-----------------------+------------------+------------------------------------------------------+
        | StatusStatus.active   | StepReplay.rerun | if in recovery and previous status is active, rerun  |
        +-----------------------+------------------+------------------------------------------------------+
        | StatusStatus.failure  | StepReplay.rerun | if in recovery and previous status is failure, rerun |
        +-----------------------+------------------+------------------------------------------------------+
        | StatusStatus.success  | StepReplay.skip  | if in recovery and previous status is success, skip  |
        +-----------------------+------------------+------------------------------------------------------+
    
    *config*: keywords mapping overrides for step configuration.
    
        +-------------------+------------------+---------------------------------------+
        | name              | default          | description                           |
        +===================+==================+=======================================+
        | stop_on_exception | True             | stop flow if step ends with Exception | 
        +-------------------+------------------+---------------------------------------+
    
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

    If there was a failure that was not followed by event triggered, result will be False.`

    


Sequent close method
--------------------

    .. code-block:: python
    
        close()
        
when calling close method, Sequentor closes open artifacts.  In concept, this is similar to Pool's close method. 

In simple example, **myflow.close()** engage Sequent's close() method.
        
Args
````

    N/A. 


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

        logger=logging.getLogger(__name__)

        def prog(flow, progname, step_to_fail=None, iteration_to_fail=''):
            step_name=flow.get_step_name() 
            step_sequence=flow.get_step_sequence()
            logger.info("doing what %s is doing (%s/%s)" % (progname, step_name, step_sequence))
            if step_to_fail == step_name and step_sequence== iteration_to_fail:
                raise Exception("%s failed (%s/%s)" % (progname, step_name, step_sequence))
            return progname

        def build_flow(run_mode=sqnt.RunMode.restart, step_to_fail=None, iteration_to_fail=''):
            myflow=sqnt.Sequent(logging_level=logging.INFO, run_mode=run_mode, 
                                config={'sleep_between_loops': 0.05,}, )

            s1=myflow.add_step('s1', repeat=[1,2])
    
            s11=s1.add_step('s11', repeat=[1,2,])
    
            s111=s11.add_step('s111', func=prog, kwargs={'flow': myflow, 'progname': 'prog1', 
                                                         'step_to_fail':step_to_fail, 
                                                         'iteration_to_fail':iteration_to_fail,}) 
            s112=s11.add_step('s112', func=prog, kwargs={'flow': myflow, 'progname': 'prog2', 
                                                         'step_to_fail':step_to_fail, 
                                                         'iteration_to_fail':iteration_to_fail,}, 
                              requires=( (s111, sqnt.StepStatus.success), )) 
    
            s12=s1.add_step('s12', func=prog, kwargs={'flow': myflow, 'progname': 'prog3', 
                                                      'step_to_fail':step_to_fail, 
                                                      'iteration_to_fail':iteration_to_fail,}, 
                            requires=( (s11, sqnt.StepStatus.success), )) 
    
            s2=myflow.add_step('s2', func=prog, kwargs={'flow': myflow, 'progname': 'prog4', 
                                                        'step_to_fail':step_to_fail, 
                                                        'iteration_to_fail':iteration_to_fail,}, 
                               requires=( (s1, sqnt.StepStatus.success), )) 
            return myflow

        # creating flow simulating failure
        myflow=build_flow(step_to_fail='s1_s11_s111', iteration_to_fail='1.2.2')
        myflow.run()
        myflow.close()

        # creating recovery flow
        myflow=build_flow(run_mode=sqnt.RunMode.recover, )
        myflow.run()
        myflow.close()
    
Example Output
--------------

    .. code:: 
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
    
    The first build and run is done in lines 42-43.  In this run, a parameter is passed to cause step *s111* in its fourth iteration to fail.  As a result, flow fails.  Output lines 1-29 is associated with the first run.  
    
    The second build and run is then initiated.  In this run, parameter is set to a value that would pass step *s111* and run mode is set to recovery (code lines 45-46). Eventor skips successful steps and start executing from failed steps onwards.  Output lines 30-40 reflects successful second run.
    
    For prog to know when to default, it uses the following methods flow.get_step_name() and flow.get_step_sequence() (lines 7-8). Those Sequent methods allow access to Eventor step attributes. Another way
    to access these attributes is via os.environ:
    
    .. code-block:: python
    
         name=os.getenv('EVENTOR_STEP_NAME')
         sequence=os.getenv('EVENTOR_STEP_SEQUENCE')
         recovery=os.getenv('EVENTOR_STEP_RECOVERY')

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

    .. code:: 
        :number-lines:
        
        import sequent as sqnt
        from acris import virtual_resource_pool as vrp

        class Resources1(vrp.Resource): pass
        class Resources2(vrp.Resource): pass
        
        rp1=vrp.ResourcePool('RP1', resource_cls=Resources1, policy={'resource_limit': 2, }).load()                   
        rp2=vrp.ResourcePool('RP2', resource_cls=Resources2, policy={'resource_limit': 2, }).load()
        
        myflow=sqnt.Sequent(logging_level=logging.INFO, config={'sleep_between_loops': 0.05,}, )
        s1=myflow.add_step('s1', repeat=[1,2], acquires=[(rp1, 2), ])
    
Additional Information
======================

    Sequent github project (https://github.com/Acrisel/sequent) has additional examples with more complicated flows.
    
    
    



 