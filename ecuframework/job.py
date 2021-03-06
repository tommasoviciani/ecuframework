import functools


@functools.total_ordering
class Job:

    """
    It is the object used to send information or tasks to the other modules.
    It is composed of parameters that carry information about the job
    """

    def __init__(self, goal, producer: str, data=None, recipient=None, priority=1, subscription=None):
        """
        :param goal: memorize the goal of the job
        :param producer: is the sender module
        :param data: it contains all the data necessary to carry out the job in Json
        :param recipient: indicates the tag of recipient module
        :param priority: is an integer value indicating the priority of the job (high priority = 1)
        :param subscription: it is a function assigned by a module that can be called at any time related to job
        """
        self.goal = goal
        self.producer = producer
        self.data = data
        self.priority = priority
        self.recipient = recipient
        self.subscription = subscription

    def __eq__(self, other):
        return self.priority == other.priority

    def __lt__(self, other):
        return self.priority < other.priority
