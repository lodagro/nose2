import traceback

from nose2 import events
from nose2.compat import unittest


class PluggableTestLoader(object):
    """Test loader that defers all loading to plugins"""

    suiteClass = unittest.TestSuite

    def __init__(self, session):
        self.session = session

    def loadTestsFromModule(self, module, use_load_tests=False):
        evt = events.LoadFromModuleEvent(self, module, use_load_tests)
        result = self.session.hooks.loadTestsFromModule(evt)
        if evt.handled:
            suite = result or self.suiteClass()
            return suite
        return self.suiteClass(evt.extraTests)

    def loadTestsFromNames(self, testNames, module=None):
        event = events.LoadFromNamesEvent(
            self, testNames,module)
        result = self.session.hooks.loadTestsFromNames(event)
        if event.handled:
            suites = result or []
        else:
            suites = [self.loadTestsFromName(name, module)
                      for name in event.names]
        if event.extraTests:
            suites.extend(event.extraTests)
        return self.suiteClass(suites)

    def loadTestsFromName(self, name, module=None):
        event = events.LoadFromNameEvent(self, name, module)
        result = self.session.hooks.loadTestsFromName(event)
        if event.handled:
            suite = result or self.suiteClass()
            return suite
        return self.suiteClass(event.extraTests)

    def failedImport(self, name):
        message = 'Failed to import test module: %s' % name
        if hasattr(traceback, 'format_exc'):
            # Python 2.3 compatibility
            # format_exc returns two frames of discover.py as well
            message += '\n%s' % traceback.format_exc()
        print message
        return self._makeFailedTest(
            'ModuleImportFailure', name, ImportError(message))

    def failedLoadTests(self, name, exception):
        return self._makeFailedTest('LoadTestsFailure', name, exception)

    def _makeFailedTest(self, classname, methodname, exception):
        def testFailure(self):
            raise exception
        attrs = {methodname: testFailure}
        TestClass = type(classname, (unittest.TestCase,), attrs)
        return self.suiteClass((TestClass(methodname),))
