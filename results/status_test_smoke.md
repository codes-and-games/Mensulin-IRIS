# Run status (test, smoke)

| experiment | pipeline_status | evidence_status | run_id | what unblocks it / note |
| --- | --- | --- | --- | --- |
| M6_circadian_recovery | exists | unchanged: a completed run with this exact config exists today | - | if INPUT DATA changed since, delete that run folder under results/runs/ and re-run (run ids hash the config, not the data) |
