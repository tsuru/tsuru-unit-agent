tsuru-unit-agent
================

roadmap 0
---------

on app start:

get envs -> inject envs -> execute start cmd.

roadmap 1
---------

on app start:

get envs -> inject envs -> pre restart hook -> execute start cmd - post restart hook.

roadmap 2
---------

on app start:

get envs -> inject envs -> pre restart hook -> execute start cmd - post restart hook -> send status to tsuru api.
