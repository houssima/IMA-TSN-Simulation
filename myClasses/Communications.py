import random
import myClasses.Event as Event

class Communications:
    def __init__(self) -> None:
        self.FCList = []

    def reset(self):
        for FC in self.FCList:
            for f in FC.flowList:
                f.reset()

class FunctionnalChain:
    def __init__(self,coms, LatencyMeasured = True):
        coms.FCList.append(self)
        self.dataList = []
        self.flowList = []
        self.PrecRelation = []
        self.LatencyMeasured = LatencyMeasured

    def findInitFlows(self):
        initFlows = []
        for f in self.flowList:
            if f.dataEntry: initFlows.append(f)
        return initFlows
    
    def findTermFlows(self):
        termFlows= self.flowList.copy()
        for pr in self.PrecRelation:
            if self.flowFromID(pr[0]) in termFlows:
                termFlows.remove(self.flowFromID(pr[0]))
        return termFlows

    def flowFromID(self,flowID):
        for f in self.flowList:
            if f.id == flowID: return f


class Flow:
    def __init__(self,id,task,message,FC):
        ############ Model
        FC.flowList.append(self)
        self.id = id
        self.task = task
        self.message = message
        self.dataEntry = None
        self.flowTree = []
        self.FuncChain = FC
        self.nbInstances = 0

        self.task.flow = self

        ########### Representation
        self.nextData = [] #represents the set of data instance that will be carried by the next instance of this flow
        self.color = [random.randint(0,255)/256,random.randint(0,255)/256,random.randint(0,255)/256]
    
    def reset(self):
        self.nbInstances = 0
        self.nextData = []

    def __repr__(self):
        return " flow_{} generating instance {} with data".format(self.id,self.nbInstances,self.nextData)
    
    def generateMessage(self):
        if self.dataEntry:
            self.nextData = [DataInstance(self.dataEntry,self.nbInstances,self)]
        newMessage = FlowInstance(self,[],self.nbInstances)
        self.nbInstances += 1
        return newMessage
    
    def nextLinks(self,link):
        nextHops = []
        if link.linkType != "CPU":
            for l in self.flowTree:
                if l.linkType != "CPU" and l.src == link.dst and l != link:
                    nextHops.append(l)
        
        elif link.linkType == "CPU":
            for l in self.flowTree:
                if l.linkType == "DMA" and l.src == link.dst and l != link:
                    nextHops.append(l)
            
        return nextHops
    
    def findNextFlow(self,link):
        nextFlowsID = []
        for pr in self.FuncChain.PrecRelation:
            if pr[0] == self.id:
                nextFlowsID.append(pr[1])
        nextFlows = []
        for f in self.FuncChain.flowList:
            if f.id in nextFlowsID and f != self:
                if f.flowTree[0].src == link.dst:
                    nextFlows.append(f)
        return nextFlows

    def refreshData(self,carriedData):
        for d in self.nextData:
            for d1 in carriedData:
                if d.path == d1.path:
                    self.nextData.remove(d)
        for d in carriedData:
            self.nextData.append(d.copy())

        for d in carriedData:
            d.path.append(self)
    
    def provideData(self,instance):
        instance.carriedData = [d.copy() for d in self.nextData]

class QueuingFlow(Flow):
    def __init__(self, id, task, message, FC):
        Flow.__init__(self,id, task, message, FC)
    
    def generateMessage(self):
        if self.dataEntry:
            self.nextData = [DataInstance(self.dataEntry,self.nbInstances,self)]
        newMessage = FlowInstance(self,[],self.nbInstances)
        self.nbInstances += 1
        return newMessage  

    def provideData(self,instance):
        sources = []
        for d in self.nextData:
            if d.path not in sources:
                sources.append(d.path)
                instance.carriedData.append(d)
                self.nextData.remove(d)


    def refreshData(self,carriedData):
        self.nextData += carriedData
        for d in carriedData:
            d.path.append(self)

class MultiFlow:
    def __init__(self):
        self.flows = []

class Message:
    def __init__(self,len,prio):
        self.size = len
        self.prio = prio
    

class FlowInstance:
    def __init__(self,flow,data,instanceNumber):
        self.flow = flow
        self.carriedData = data
        self.time_since_arrival = 0
        self.instanceNumber = instanceNumber
    
    def acquireData(self):
        self.flow.provideData(self)    

    def onNewLink(self):
        return FlowInstance(self.flow,self.carriedData,self.instanceNumber)

    def __repr__(self) -> str:
        return " f_{}^{} carrying {}".format(self.flow.id,self.instanceNumber,self.carriedData)

    def __str__(self) -> str:
        return " f_{}^{} carrying {}".format(self.flow.id,self.instanceNumber,self.carriedData)

class Task:
    def __init__(self,period, execTime, deadline, offset, prio):
        self.period = period
        self.execTime = execTime
        self.deadline = deadline
        self.offset = offset
        self.prio = prio
        self.flow = None

class TaskEventTriggered(Task):
    def __init__(self,event,execTime,deadline,offset,prio):
        Task.__init__(self, 0, execTime, deadline,offset,prio)
        self.trigger = event
    
    def istrigger(self, event):
        if event.instance.flow == self.trigger.instance.flow and event.eventType == self.trigger.eventType:
            return Event.Event(event.refTime, self.flow.flowTree[0], self.flow.generateMessage(), "Arrival")

class PTP(TaskEventTriggered):
    def __init__(self, event, execTime, deadline, offset, prio):
        super().__init__(event, execTime, deadline, offset, prio)

    def istrigger(self, event):
        if event.instance.flow == self.trigger.instance.flow and event.eventType == self.trigger.eventType:
            l = event.instance.flow.flowTree[0]
            l.dst.synchronisation(l.src.currentTime) 
            return Event.Event(event.refTime, self.flow.flowTree[0], self.flow.generateMessage(), "Arrival")



class Data:
    def __init__(self,FC,flow):
        FC.dataList.append(self)
        self.id = flow

class DataInstance:
    def __init__(self, data, instanceNumber, sourceFlow):
        self.data = data
        self.instanceNumber = instanceNumber
        self.path = [sourceFlow]

    def __repr__(self) -> str:
        return " d_{}^{}".format(self.data.id,self.instanceNumber)

    def __str__(self) -> str:
        return " d_{}^{}".format(self.data.id,self.instanceNumber)
    
    def copy(self):
        new = DataInstance(self.data,self.instanceNumber,None)
        new.path = self.path.copy()
        return(new)
    

