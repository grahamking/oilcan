#!/usr/bin/python
"""Task manager for Gearman.
"""

# Copyright 2010 Graham King <graham@gkgk.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# For the full licence see <http://www.gnu.org/licenses/>.

# pylint: disable-msg=R0201

import sys
import logging
import argparse
from multiprocessing import Process

from gearman.libgearman import Worker, GEARMAN_SUCCESS, GEARMAN_TIMEOUT

TIMEOUT = 5000     # milli-seconds
LOGGER = logging.getLogger('oilcan')


def task(func):
    """Decorator that marks given function as an Oilcan task"""
    LOGGER.debug('Oilcan: Decorator ran for %s', func)
    func.is_oilcan_task = True
    return func


class OilcanWorker(Process):
    """Runs in a sub-process. There can be lots of these.
    Listens for Gearman messages and runs tasks.
    """

    def __init__(self, task_module, servers):
        super(OilcanWorker, self).__init__()

        self.task_module = task_module
        self.servers = servers

        self.is_running = True
        self.worker = None
        self.task_map = {}

    def run(self):
        """Worker main method"""

        self.worker = Worker()
        for host in self.servers:
            self.worker.add_server(host)

        self.register_tasks(self.task_module)

        # self.worker.work() blocks in libgearman.so,
        # so make it time out occasionally and give back control.
        self.worker.set_timeout(TIMEOUT)

        while self.is_running:              # is_running is always True
            result = self.worker.work()
            if result not in [GEARMAN_SUCCESS, GEARMAN_TIMEOUT]:
                LOGGER.warn('Oilcan: Gearman task result code: %d', result)

    def register_tasks(self, task_module):
        """Inspect task_module and records the tasks it finds.
        Tasks are a function with an is_oilcan_task attribute.
        Usually this attribute is set via the @tasks decorator.
        """

        system_import(task_module)
        tasks = sys.modules[task_module]
        LOGGER.debug('Oilcan: Imported: %s', tasks)

        for name in dir(tasks):
            if name.startswith('__'):
                continue

            func = getattr(tasks, name)
            if hasattr(func, 'is_oilcan_task'):
                self.task_map[name] = func
                self.worker.add_function(name, self.run_task)
                LOGGER.debug('Oilcan: Registered task "%s"', name)

        if not self.task_map:
            LOGGER.error('Oilcan: No tasks found in module "%s"', 
                    self.task_module)
            return

    def run_task(self, job):
        """Called by Gearman"""
        func = self.task_map[job.function_name()]
        workload = job.get_workload()

        func_log = '%s(%s)' % (func.__name__, workload)
        LOGGER.debug('Oilcan: Running task: %s', func_log)

        ret = None
        try:
            ret = func(workload)
        except Exception:       # pylint: disable-msg=W0703
            job.send_fail()
            LOGGER.exception('Exception calling %s', func_log)

        # Gearman tasks must return a string result
        return "OK" if not ret else str(ret)


class OilcanManager(object):
    """Starts and stops the worker sub-processes"""

    DEFAULT_GEARMAN_SERVERS = ["127.0.0.1"]

    def __init__(self):

        self.servers = OilcanManager.DEFAULT_GEARMAN_SERVERS

        self.task_module = None
        self.num_processes = None
        self.is_fork = True

    def start_workers(self):
        """Creates OilcanWorker sub-processes.
        
        @param servers: Array of string IP addresses, where the Gearman 
            servers are. e.g. servers=["127.0.0.1"]
        @param num_processes: How many processes to start. 
            Number of processors (cores) + 1 is a good starting point.
        @param is_fork: Should we fork off sub-processes. Defaults to True.
            Only set to False for debugging.
        """

        LOGGER.debug('Oilcan: Starting workers. ' +
                        'task_module=%s, servers=%s, num_processes=%d',
                        self.task_module, self.servers, self.num_processes)

        if not self.is_fork:
            # Debug mode - just run it
            LOGGER.debug('Oilcan: Running in non-forked mode')
            try:
                proc = OilcanWorker(self.task_module, self.servers)
                proc.run()
            except Exception:   # pylint: disable-msg=W0703
                LOGGER.exception('Exception running non-forked oilcan')
            LOGGER.debug('no-fork client finished')
            return

        # Normal mode - Start sub-processes

        process_list = []
        for _ in range(self.num_processes):
            proc = OilcanWorker(self.task_module, self.servers)
            proc.start()
            process_list.append(proc)

        LOGGER.info('Oilcan: Exit')

    def add_console_handler(self):
        """Add a console handler to LOGGER. Useful for debug output"""
        handler = logging.StreamHandler(sys.stdout)
        LOGGER.addHandler(handler)
        LOGGER.setLevel(logging.DEBUG)
        LOGGER.propagate = False

        LOGGER.debug('Oilcan: DEBUG ON')

    def parse_args(self, args):
        """Parses the command line arguments, returns a Namespace,
        which looks like an object with properties:
        task_module, servers, procs, debug
        """

        parser = argparse.ArgumentParser(
                description='Start oilcan (Gearman) worker')
        
        parser.add_argument('task_module',
                help='Python module to import and look for tasks in')

        parser.add_argument('--servers', nargs='*', metavar='server',
            help='Space separated list of Gearman servers. Defaults to %s' % 
                ' '.join(OilcanManager.DEFAULT_GEARMAN_SERVERS))

        parser.add_argument('--procs', default=5, type=int,
                help='Number of processes to start')

        parser.add_argument('--add-path', nargs='*', metavar='path',
                help='Add these directories to the PYTHONPATH')

        parser.add_argument('--no-fork', action='store_false', dest='is_fork', 
                default=True,
                help='No subprocesses. Useful for debugging.')

        parser.add_argument('--debug', action='store_true', default=False,
                help='Output debug info to console')

        if len(args) <= 1:
            parser.error('Missing task_module argument')

        return parser.parse_args(args)

    def main(self):
        """Called from command line as script, starts workers"""

        args = self.parse_args(sys.argv[1:])

        self.task_module = args.task_module
        self.num_processes = args.procs
        self.is_fork = args.is_fork

        if args.servers:
            self.servers = args.servers

        if args.debug:
            self.add_console_handler()

        if args.add_path:
            sys.path.extend(args.add_path)
            LOGGER.debug('Oilcan: Python path is now: %s', sys.path)
        
        self.start_workers()


def system_import(module_name):
    """Wrapper around __import__ built-in to help with testing"""
    __import__(module_name)


if __name__ == '__main__':
    OilcanManager().main()

