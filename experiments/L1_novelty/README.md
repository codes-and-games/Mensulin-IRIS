# L1_novelty

| Field | Content |
| --- | --- |
| Purpose | Record the novelty/evidence search and force a narrower claim when close prior work exists. |
| Hypothesis | n/a |
| Inputs | Human-performed searches logged in literature/novelty_search_log.csv. |
| Source / evidence class | COMPUTED |
| Procedure | Validate the log; extract near neighbours. |
| Variables | database, query |
| Controls | empty log => BLOCKED |
| Metrics | n searches, near-neighbour count |
| Expected outputs | search_log, near_neighbours |
| Interpretation | Novelty is not assumed. |
| Failure conditions | no searches logged; close prior study without a narrowed claim |

Run: `python -m iris.tools.run_experiment L1_novelty [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
