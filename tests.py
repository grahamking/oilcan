#!/usr/bin/python
"""Unit tests for Oilcan.
"""

# pylint: disable-msg=R0201

from unittest import TestCase, main
from mocker import Mocker, expect

import oilcan


class TestManager(TestCase):
    """Test OilcanManager"""

    def test_task(self):
        """Test the @task decorator"""
        test_func = lambda x: x 

        ret = oilcan.task(test_func)

        # Decorator returns what we gave it..
        self.assertEqual(ret, test_func)
        # ..having added an is_oilcan_task attribute..
        self.assertTrue(hasattr(test_func, 'is_oilcan_task'))
        # .. which is True
        self.assertTrue(test_func.is_oilcan_task)

    def test_create(self):
        """Tests constructors"""

        manager = oilcan.OilcanManager()
        self.assertTrue(manager.servers)

    def test_add_console_handler(self):
        """There's nothing really to test in the method,
        so just run it, check it's valid Python"""

        manager = oilcan.OilcanManager()
        manager.add_console_handler()

    def test_parse_args(self):
        """Tests command line argument parsing"""

        args = '--servers 127.0.0.1 192.168.0.1 --procs 3 package.tasks'\
                .split()
        manager = oilcan.OilcanManager()
        parsed = manager.parse_args(args)

        self.assertEqual(parsed.procs, 3)
        self.assertEqual(parsed.task_module, 'package.tasks')
        self.assertEqual(parsed.servers, ['127.0.0.1', '192.168.0.1'])


class TestWorker(TestCase):
    """Test OilcanWorker"""

    def test_create(self):
        """Tests constructor"""

        tasks = object()
        servers = ["127.0.0.1"]
        worker = oilcan.OilcanWorker(tasks, servers)
        self.assertEqual(tasks, worker.task_module)
        self.assertEqual(servers, worker.servers)

    def test_run_task_success(self):
        """Tests run_task when it works"""

        mocker = Mocker()

        mock_job = mocker.mock()
        expect(mock_job.function_name()).result('test_func')
        expect(mock_job.get_workload()).result(42)

        mock_func = mocker.mock()
        expect(mock_func.__name__).result('test_func')
        expect(mock_func(42)).result('OK')
        
        worker = oilcan.OilcanWorker(None, None)
        worker.task_map['test_func'] = mock_func

        with mocker:
            self.assertEqual(worker.run_task(mock_job), 'OK')

    def test_run_task_fail(self):
        """Tests run_task when the task raises an Exception"""

        mocker = Mocker()

        mock_job = mocker.mock()
        expect(mock_job.function_name()).result('test_func')
        expect(mock_job.get_workload()).result(42)
        expect(mock_job.send_fail())

        mock_func = mocker.mock()
        expect(mock_func.__name__).result('test_func')
        expect(mock_func(42)).throw(ValueError())
        
        worker = oilcan.OilcanWorker(None, None)
        worker.task_map['test_func'] = mock_func

        with mocker:
            worker.run_task(mock_job)

    def test_register_tasks(self):
        """Test register_tasks"""

        class DummyModule(object):
            """Module we import and look for tasks on"""

            def func_one(self):
                """Oilcan task"""
                pass
            func_one.is_oilcan_task = True

            def func_two(self):
                """Not oilcan task"""
                pass

        worker = oilcan.OilcanWorker(None, None)

        mocker = Mocker()
        mock_import = mocker.mock()
        expect(mock_import('test_module'))
        oilcan.system_import = mock_import

        mock_sys_modules = mocker.replace('sys.modules')
        dummy_module = DummyModule()
        expect(mock_sys_modules['test_module']).result(dummy_module)

        mock_gearman_worker = mocker.mock()
        expect(mock_gearman_worker.add_function('func_one', worker.run_task))
        worker.worker = mock_gearman_worker

        with mocker:
            worker.register_tasks('test_module')

        self.assertEqual(len(worker.task_map), 1)
        self.assertTrue('func_one' in worker.task_map)
        self.assertEqual(worker.task_map['func_one'], dummy_module.func_one)


if __name__ == '__main__':
    main()

