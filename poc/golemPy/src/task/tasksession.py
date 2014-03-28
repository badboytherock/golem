from message import MessageWantToComputeTask, MessageTaskToCompute, MessageCannotAssignTask, MessageTaskComputed
from taskcomputer import TaskComputer
import time

class TaskSession:

    ##########################
    def __init__( self, conn, taskServer, address, port ):
        self.conn           = conn
        self.taskServer     = taskServer
        self.taskManager    = taskServer.taskManager
        self.taskComputer   = taskServer.taskComputer
        self.address        = address
        self.port           = port

    ##########################
    def askForTask( self, taskId, performenceIndex ):
        self.conn.sendMessage( MessageWantToComputeTask( taskId, performenceIndex ) )

    ##########################
    def sendTaskResults( self, id, extraData, taskResult ):
        self.conn.sendMessage( MessageTaskComputed( id, extraData, taskResult ) )

    ##########################
    def interpret( self, msg ):
        if msg is None:
            pass #TODO

        type = msg.getType()

        #localtime   = time.localtime()
        #timeString  = time.strftime("%H:%M:%S", localtime)
        #print "{} at {}".format( msg.serialize(), timeString )

        if type == MessageWantToComputeTask.Type:

            taskId, srcCode, extraData = self.taskManager.getNextSubTask( msg.taskId, msg.perfIndex )

            if taskId != 0:
                self.conn.sendMessage( MessageTaskToCompute( taskId, extraData, srcCode ) )
            else:
                self.conn.sendMessage( MessageCannotAssignTask( taskId, "No more subtasks in {}".format( msg.taskId ) ) )

        elif type == MessageTaskToCompute.Type:
            self.taskComputer.taskGiven( msg.taskId, msg.sourceCode, msg.extraData )
            self.dropped()

        elif type == MessageCannotAssignTask.Type:
            self.taskComputer.taskRequestRejected( msg.taskId, msg.reason )
            self.dropped()

        elif type == MessageTaskComputed.Type:
            self.taskServer.taskManager.computedTaskReceived( msg.id, msg.extraData, msg.result )
            # Add message with confirmation that result is accepted
            self.dropped()

    def dropped( self ):
        self.conn.close()
        self.taskServer.removeTaskSession( self )