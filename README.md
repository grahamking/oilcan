
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
    for host, port in [("127.0.0.1", 4730), ("192.168.0.100", 4730)]:
        client.add_server(host, port)

    # Call
    # Workload ('42') must be a string. 
    client.do_background('example_task', '42')

If `do` or `do_background` return a response code, it's an index into a gearman_return_t enum. To find out what it means, count into this list, starting from 0: http://gearman.org/docs/api/group__gearman__constants.html#g200f3d324fd4c4bfee16143c8f7b672a

## Install ##

1. Get the dependencies 

    **Ubuntu 10.10 (Maverick) and later**

        sudo apt-get install gearman-job-server python-gearman.libgearman

    **Other Linuxes**

    Make sure you have the dependencies: 
    
        sudo apt-get install libevent-dev uuid-dev

    The `python-gearman.libgearman` package isn't in earlier version of Ubuntu, and the PyPI version relies on a recent Gearman, so install both:

        wget http://launchpad.net/gearmand/trunk/0.14/+download/gearmand-0.14.tar.gz
        tar xvzf gearmand-0.14.tar.gz
        cd gearmand-0.14
        ./configure --disable-libmemcached
        sudo make install

        sudo pip install python-libgearman

    You might not need to disable libmemcached, but I got three of this type of error if I didn't: _gearmand-0.14/gearmand/gearmand.c:193: undefined reference to `gearman_server_queue_libmemcached_conf'_.

    You might also need to: `sudo apt-get install libgearman2 ; sudo ldconfig`, but don't ask me why.

2. If you're running Python 2.6 or earlier you need the argparse package. It's in the standard library for 2.7+:

        sudo pip install argparse

3. Get oilcan (cd into a temporary directory first):

        git clone git://github.com/grahamking/oilcan.git
    
4. Copy oilcan.py onto your python path:

        sudo cp oilcan.py /usr/local/lib/python2.6/site-packages/
    
5. Link it from /usr/local/bin/:

        sudo ln -s /usr/local/lib/python2.6/site-packages/oilcan.py /usr/local/bin/oilcan

6. Copy the [upstart](http://upstart.ubuntu.com/) startup script into /etc/init/:

        sudo cp oilcan.conf /etc/init/

7. Edit /etc/init/oilcan.conf and make it work for you. 

        vim /etc/init/oilcan.conf   # Or your editor of choice

    For help on this run:

        /usr/local/bin/oilcan --help

8. Start the worker (Gearman must already be running):

        sudo start oilcan

## Tests ##

Oilcan ships with some unit tests in the _tests_ file. To run them you need:

- Nose: _python-nose_ in Ubuntu, or _nose_ in PyPI.
- Coverage: _python-coverage_ in Ubuntu, or _coverage_ in PyPI.

Run like this, from the directory that contains tests.py and oilcan.py:

    nosetests --with-coverage --cover-package=oilcan tests.py

## Debug ##

If there is an error in your tasks.py oilcan will die as soon as it starts. To see what's going on, run oilcan in non-forked debug mode:

    export DJANGO_SETTINGS_MODULE=settings  # Only needed if using Django
    /usr/local/bin/oilcan myapp.tasks --add-path /usr/local/myproj/ --no-fork --debug

## Using supervisord, or any other process manager ##

If you prefer something other than _upstart_, simply copy the command from `/etc/init/oilcan.conf`. Oilcan doesn't daemonize itself, so it should play nicely with any process manager you care to use.

## MySQL binlog error ##

If you are using MySQL InnoDB, you might get this error:

    OperationalError: (1598, "Binary logging not possible. Message: Transaction level 'READ-COMMITTED' in InnoDB is not safe for binlog mode 'STATEMENT'")

Because oilcan runs for a long time, it changes MySQL's transaction isolation mode to READ-COMMITTED, so that it sees changes. InnoDB's binary log needs to be in ROW mode to support this. In `/etc/mysql/my.cnf` add or edit this row:

    binlog-format = ROW

