from aws_lambda_powertools import Logger, Tracer

from iprs import IPRS
from kra import KRA
from lexisnexis import LexisNexis
from utiities import JubileeESBUtilities

logger = Logger()
tracer = Tracer()


class JubileeESBAPI:

    def __init__(self):
        utilities = JubileeESBUtilities()
        self.iprs = IPRS(utilities)
        self.kra = KRA(utilities)
        self.lexisnexis = LexisNexis(utilities)
