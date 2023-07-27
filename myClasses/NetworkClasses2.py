import myClasses.Communications as Coms
import myClasses.Nodes as Nodes
import myClasses.Link as Link
import myClasses.Event as Event
import myClasses.Policies as Policies
from random import gauss


class PhysicalNetwork:
    def __init__(self,name):
        self.name = name
        self.nb_links = 0
        self.links = []
        self.Elements = []
    
    def reset(self):
        for e in self.Elements:
            e.reset()
    
    def randomOffset(self,sigma = 0.001):
        for e in self.Elements:
            if e.ToTimeUpdate:
                e.currentTime = gauss(0,sigma)

    def randomDrift(self,sigma = 0.000001):
        for e in self.Elements:
            if e.ToTimeUpdate:
                e.drift = gauss(1,sigma)

    def periodicSync(self, MasterID, BoundaryList, period, coms):
        
        syncTaskReq = Coms.Task(period, 0.01, period, 0, 4)
        syncReq = Coms.Message(20,7)
        syncReply = Coms.Message(20,7)
        syncData = Coms.Message(100,7)
        
        flowID = sum([len(funcChain.flowList) for funcChain in coms.FCList])
        for e in self.Elements:
            if isinstance(e,Nodes.Node):
                if e.id == MasterID:
                    e.PTP_Profile = "Master"
                elif e.id in BoundaryList:
                    e.PTP_Profile = "Boundary"
                    found = False
                    for l in self.links:
                        if l.src.id == e.id and l.dst.id == MasterID:
                            S2M = l
                            found = True
                        if l.src.id == MasterID and l.dst.id == e.id:
                            M2S = l
                            found = True
                    if not found:
                        for l in self.links:
                            if l.src.id == e.id and l.dst.id in BoundaryList:
                                S2M = l
                            if l.src.id in BoundaryList and l.dst.id == e.id:
                                M2S = l
                    syncFC = Coms.FunctionnalChain(coms,False)
                    # PTP request
                    syncFlowReq = Coms.Flow(flowID,syncTaskReq,syncReq,syncFC)
                    flowID += 1 
                    syncFlowReq.flowTree = [M2S]
                    #PTP reply 
                    trigger = Event.Event(0,M2S,syncFlowReq.generateMessage(),"endOfDelivery")
                    syncTaskReply = Coms.TaskEventTriggered(trigger, 0.01, period,0,4)
                    syncFlowRep = Coms.Flow(flowID,syncTaskReply,syncReply,syncFC)
                    flowID += 1 
                    syncFlowRep.flowTree = [S2M]
                    #PTP data reply ()
                    trigger = Event.Event(0,S2M,syncFlowRep.generateMessage(),"endOfDelivery")
                    syncTaskData = Coms.TaskEventTriggered(trigger, 0.01, period,0,4)
                    syncFlowData = Coms.Flow(flowID,syncTaskData,syncData,syncFC)
                    flowID += 1 
                    syncFlowData.flowTree = [M2S]
                else:
                    e.PTP_Profile = "Slave"
                    for l in self.links:
                        if l.src.id == e.id and l.dst.id in BoundaryList + [MasterID]:
                            S2M = l
                        if l.src.id in BoundaryList + [MasterID] and l.dst.id == e.id:
                            M2S = l
                    syncFC = Coms.FunctionnalChain(coms)
                    # PTP request
                    syncFlowReq = Coms.Flow(flowID,syncTaskReq,syncReq,syncFC)
                    flowID += 1 
                    syncFlowReq.flowTree = [M2S]
                    #PTP reply 
                    trigger = Event.Event(0,M2S,syncFlowReq.generateMessage(),"endOfDelivery")
                    syncTaskReply = Coms.TaskEventTriggered(trigger, 0.01, period,0,4)
                    syncFlowRep = Coms.Flow(flowID,syncTaskReply,syncReply,syncFC)
                    flowID += 1 
                    syncFlowRep.flowTree = [S2M]
                    #PTP data reply ()
                    trigger = Event.Event(0,S2M,syncFlowRep.generateMessage(),"endOfDelivery")
                    syncTaskData = Coms.TaskEventTriggered(trigger, 0.01, period,0,4)
                    syncFlowData = Coms.Flow(flowID,syncTaskData,syncData,syncFC)
                    flowID += 1 
                    syncFlowData.flowTree = [M2S]


    def linkID(self):
        a = self.nb_links
        self.nb_links+=1
        return a

    def timeUpdate(self,timeShift):
        for e in self.Elements:
            if e.ToTimeUpdate :
                e.timeUpdate(timeShift)

    def findElement(self,netClass,id):
        for el in self.Elements:
            if isinstance(el, netClass):
                if el.id == id:
                    return(el)
        

            