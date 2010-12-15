
**oilcan** is a Python job manager for Gearman. It is intended as an alternative for Celery, when your queuing system of choice is Gearman, and you want something simple.

Concept:

 1. You use a decorator to mark which python functions can be called as a task.
 2. You start oilcan, pointing it at a file cointaining tasks. It forks worker sub-processes.
 3. You send a message to Gearman to trigger one of the jobs.

**oilcan** is alpha software, not quite ready yet.

## Example ##

To define some tasks you do this (by convention in a tasks.py file):

    from oilcan import task

    @task
    def example_task(self, workload):

        # Workload is whatever string the client sent
        do_something(workload)

To call that task:

    # Setup
    from gearman.libgearman import Client
    client = Client()
    for host in ["127.0.0.1", "192.168.0.100"]:
        client.add_server(host)

    # Call
    # Workload ('42') must be a string. 
    client.do_background('example_task', '42')

## Install ##

Get the dependencies:

    sudo apt-get install gearman-job-server python-gearman.libgearman

Copy oilcan.py onto your python path:

    sudo cp oilcan.py /usr/local/lib/python2.6/dist-packages/
    
Link it from /usr/local/bin/:

    sudo ln -s /usr/local/lib/python2.6/dist-packages/ /usr/local/bin/oilcan

Copy the startup script into /etc/init/. It is an upstart script.

    sudo cp oilcan.conf /etc/init/

Edit /etc/init/oilcan.conf and make it work for you. For help on this run:

    /usr/local/bin/oilcan --help

Start the worker (Gearman must already be running):

    sudo start oilcan

MORE DOCS TO COME.

