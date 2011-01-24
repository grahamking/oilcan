#!/usr/bin/python
"""Unit tests for Oilcan.
"""

from unittest import TestCase, main

import oilcan


class TestOilcan(TestCase):
    """Test"""

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
        """Tests that we can create both our objects"""

        manager = oilcan.OilcanManager()
        self.assertTrue(manager.servers)

        tasks = object()
        servers = ["127.0.0.1"]
        worker = oilcan.OilcanWorker(tasks, servers)
        self.assertEqual(tasks, worker.task_module)
        self.assertEqual(servers, worker.servers)
        

if __name__ == '__main__':
    main()

