import random
import logging
import cPickle as pickle

from golem.manager.client.NodesManagerClient import NodesManagerClient
from golem.environments.Environment import Environment
from golem.task.TaskBase import ComputeTaskDef, result_types
from GNRTask import GNRTask, GNRTaskBuilder

logger = logging.getLogger(__name__)

##############################################
class InfoTaskDefinition:
    def __init__(self):
        self.taskId = ""

        self.fullTaskTimeout    = 0
        self.subtaskTimeout     = 0

        self.srcFile            = ""
        self.totalSubtasks      = 0

        self.manager_address     = ""
        self.manager_port        = 0

##############################################
class InfoTaskBuilder(GNRTaskBuilder):

    def build(self):
        with open(self.taskDefinition.srcFile) as f:
            srcCode = f.read()
        return InfoTask(   srcCode,
                            self.client_id,
                            self.taskDefinition.taskId,
                            "",
                            0,
                            "",
                            Environment.getId(),
                            self.taskDefinition.fullTaskTimeout,
                            self.taskDefinition.subtaskTimeout,
                            0,
                            0,
                            self.taskDefinition.manager_address,
                            self.taskDefinition.manager_port,
                            self.taskDefinition.totalSubtasks
                          )

##############################################
class InfoTask(GNRTask):

    def __init__(self,
                  srcCode,
                  client_id,
                  taskId,
                  ownerAddress,
                  ownerPort,
                  ownerKeyId,
                  environment,
                  ttl,
                  subtaskTtl,
                  resourceSize,
                  estimatedMemory,
                  nodesManagerAddress,
                  nodesManagerPort,
                  iterations):


        GNRTask.__init__(self, srcCode, client_id, taskId, ownerAddress, ownerPort, ownerKeyId, environment,
                            ttl, subtaskTtl, resourceSize, estimatedMemory)

        self.totalTasks = iterations

        self.nodesManagerClient = NodesManagerClient(nodesManagerAddress, int(nodesManagerPort))
        self.nodesManagerClient.start()

    #######################
    def abort (self):
        self.nodesManagerClient.dropConnection()

    #######################
    def queryExtraData(self, perfIndex, num_cores, client_id = None):
        ctd = ComputeTaskDef()
        ctd.taskId = self.header.taskId
        hash = "{}".format(random.getrandbits(128))
        ctd.subtaskId = hash
        ctd.extraData = {
                          "startTask" : self.lastTask,
                          "endTask": self.lastTask + 1 }
        ctd.returnAddress = self.header.taskOwnerAddress
        ctd.returnPort = self.header.taskOwnerPort
        ctd.taskOwner = self.header.taskOwner
        ctd.shortDescription = "Standard info Task"
        ctd.srcCode = self.srcCode
        ctd.performance = perfIndex
        if self.lastTask + 1 <= self.totalTasks:
            self.lastTask += 1

        return ctd

    #######################
    def computationFinished(self, subtaskId, taskResult, dirManager = None, resultType = 0):
        if resultType != result_types['data']:
            logger.error("Only data result format supported")
            return
        try:
            msgs = pickle.loads(taskResult)
            for msg in msgs:
                self.nodesManagerClient.sendClientStateSnapshot(msg)
        except Exception as ex:
            logger.error("Error while interpreting results: {}".format(str(ex)))

    #######################
    def prepare_resourceDelta(self, taskId, resourceHeader):
        return None
