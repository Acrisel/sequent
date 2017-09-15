
====================
Sequent Design Notes
====================

--------------------------
Complex design made simple
--------------------------



Hostesizing
===========

Sequent uses a process we are calling *Hostesizing* to rebuild Sequent flow implying hosts associated with *Steps*.  *Hostesozing* would translate each Meta step associated to two or more hosts, adding Sub-Meta step for each host.

.. code-block:: python
 
        +--S1----------------------------+
        |                                |
        | +--S11-(H1, H2)-+              |
        | |               |              |
        | | S111  -> S112 | -> S12 (H1)  | 
        | +---------------+              |
        +--------------------------------+

In the above structure, S11 and S12 are associated with hosts to run on. *Hostesizing* would translate S11 to two Meta steps one for H1 and another for H2. 

.. code-block:: python

        +--S1-------------------------------+
        |                                   |
        | +--S11-(H1)-----+                 |
        | |               |                 |
        | | S111  -> S112 | -> +----------+ | 
        | +---------------+    |          | |
        |                      | S12 (H1) | | 
        | +--S11-(H2)-----+    |          | |
        | |               | -> +----------+ | 
        | | S111  -> S112 |                 | 
        | +---------------+                 |
        +-----------------------------------+

The new constructions S12 requires would be adjusted to include *S11-H1* and *S11-H2*.