## What is multidb
It's a very simple REPL DB client, which allows to lunch multiple queries on the same target, OR multiple queries on multiple targets, with a single command.
It is meant for people who manage many DBs and need to run the same queries on all of them

## Setting up dev environment
<h6> if you are not using docker, please use docker! We are in 2024 :) </h6>

```docker compose up --build -d```


## Export the executable file
Once inside the docker container, run the following command
```pyinstaller --onefile --name multidb main.py```

## How to use
Create a file called "connections.json" and save it in the same fodler of the executable, according to "connections_sample.json" structure.
Once opened the REPL session, by running ```python main.py``` or directly the binaary, these are the commands available (not case sensitive):
1. ```USE```: it shows the available connections loaded from the "connections.json" file
2. ```USE <list of connections, comma separated>```: it connects to the given list of connections. queries executed from now on will be executed on all the active connections
3. ```USED```: it shows active connections
4. ```CLEAR```: clear the terminal
5. ```EXIT```: leave the REPL session
6. ```RELOAD```: reload the "connections.json" file, without the need to exit/enter the REPL session
7. ```DISCONNECT```: close all the active connections
8. ```QUERY <queries, comma separated>```: executes one or more queries, in sequence, for all the active connections
9. ```QUERY <queries, comma separated>```: same as ```query``` but output is redirected to a file in the current folder
