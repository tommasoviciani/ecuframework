import threading
import logging
import queue

from ecuframework.util import looped


class Receiver:
    """
    Allows communication between modules and MCU.
    This class is stored in the modules when they are registered in the MCU
    """
    def __init__(self, mcu_instance, on_receiver):
        """
        :param mcu_instance: it is the instance of the MCU to which the Jobs must be sent
        :param on_receiver: it is the function that deals with Job
        """
        self._mcu_instance = mcu_instance
        self._on_receiver = on_receiver

    def get(self, job):
        """
        It obtains the sender's job passed to it as input and sends it to the recipient receiver
        :param job: assigned by the sender
        :return: None
        """
        self._on_receiver(self._mcu_instance, job)


class Mcu(threading.Thread):

    """
    MCU (Modules Central Unit)
    It is the main object that manages the communication between the modules.
    It is very important because it gives a common base to all processes
    by offering the shared queue administered by the McuController
    """

    class Pattern:

        """
        The McuPattern object is used to store the decorated methods in the MCU.
        If we want to use this scheme we need to initialize it as a class attribute in the inherited MCU
        """

        def __init__(self):
            self._handler_functions = {
                'on_receiver': None,
                'assigning_job': None,
            }

        def on_receiver(self):
            def decorator(f):
                self._handler_functions['on_receiver'] = f

            return decorator

        def assigning_job(self):
            def decorator(f):
                self._handler_functions['assigning_job'] = f

            return decorator

    class _Controller:

        """
        It is the class that manages all MCU entirely
        """

        # Stores the MCU pattern. Through this access is made to methods decorated with the support of McuPattern objects
        _pattern = {}

        # Instance of the MCU
        _mcu_instance = None

        # It is the receiver object that will be used to receive jobs from the modules
        _receiver = None

        # Is the list of modules currently registered on the MCU
        _modules = []

        def __init__(self, mcu_instance):
            self._mcu_instance = mcu_instance

        def get_pattern(self):
            return self._pattern

        def get_mcu_instance(self):
            return self._mcu_instance

        def add_module(self, module):
            self._modules.append(module)

        def modules(self):
            return self._modules

        def receiver(self):
            return self._receiver

        def get_recipient_module(self, function):
            """
            It is the method that obtains the recipient of a particular module based on the basic rule,
            that is, the search based on the type of module
            :param function: rule for searching the module
            :return: recipient module if it exists, otherwise it returns None
            """
            filtered = list(filter(function, self._modules))
            return filtered[0] if len(filtered) > 0 else None

        def register_pattern(self, mcu_pattern):
            on_receiver = mcu_pattern.__dict__['_handler_functions'].pop('on_receiver')
            self._receiver = Receiver(self._mcu_instance, on_receiver)
            self._pattern = mcu_pattern.__dict__['_handler_functions']

    def __init__(self, instance, tag):
        # Call to the constructor of the Thread class.
        # By default the Mcu process is not a thread daemon
        super().__init__(name=f'Mcu[{tag}]', daemon=False)
        self.tag = tag
        self.logger = logging.getLogger(tag)
        self.controller = self._Controller(mcu_instance=instance)
        self.shared_queue = queue.PriorityQueue()

    def register_modules(self, modules):
        candidate_modules = list(dict.fromkeys(modules))

        if all(module in self.controller.modules() for module in candidate_modules):
            raise AssertionError('The modules have already been registered')

        for module in candidate_modules:
            # Here the MCU receiver is saved on the new modules to be registered
            module.controller.register_receiver(self.controller.receiver())
            self.controller.add_module(module)

    def _start_modules(self):
        if len(self.controller.modules()) == 0:
            self.logger.warning('No module to start')
        [module.start() for module in self.controller.modules()]

    def _processor(self):
        """
        It is the process that obtains jobs from the MCU queue and
        calls the method decorated with @assigning_job to assign jobs to the modules
        :return: None
        """
        job = self.shared_queue.get()
        if self.controller.get_pattern()['assigning_job']:
            self.controller.get_pattern()['assigning_job'](self.controller.get_mcu_instance(), job)
        self.shared_queue.task_done()

    def run(self):
        self.logger.info(f'Modules starting')

        if self.controller.get_mcu_instance() is None:
            raise AssertionError('The Mcu instance is None')

        looped(self._processor, daemon=False)

        self._start_modules()