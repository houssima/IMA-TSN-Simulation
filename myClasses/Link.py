import myClasses.Event as Event
import myClasses.Communications as Coms

class Link:
    def __init__(self, id, src, dst, rate,linkType,net, delay = 0):
        ######### Model
        self.src = src
        self.dst = dst
        
        self.rate = rate
        self.delay = delay
        self.linkType = linkType #DMA/CPU/NET
        self.localScheduler = None
        
        #####Running
        self.in_transmission = None
        self.channeling = []
        self.arrived = []
        self.id = id
        self.ToTimeUpdate = True
        net.Elements.append(self)
        net.links.append(self)
        net.nb_links +=1
    
    def reset(self):
        self.in_transmission = None
        self.channeling = []
        self.arrived = []

    def workload(self, flow):
        if self.linkType ==  "CPU":
            return flow.task.execTime
        else: return flow.message.size/self.rate
    
    def prio(self,flow):
        if self.linkType ==  "CPU":
            return flow.task.prio
        elif self.linkType == "DMA":
            return 0
        else: return flow.message.prio

    def timeUpdate(self,timeShift):
        for instance in self.arrived:
            instance.time_since_arrival += timeShift

    def sendDecision(self,refTime):
        newEvents = []
        instance = self.localScheduler.electMessage()
        if self.linkType == 'CPU' and instance:
            instance.acquireData()
        if instance:
            self.channeling.append(instance)
            self.in_transmission = instance
            newEvents.append(Event.Event(refTime,
                                        self,instance,"Transmission"))
            newEvents.append(Event.Event(refTime+self.delay,
                                        self,instance,"Delivery"))
            newEvents.append(Event.Event(refTime+self.workload(instance.flow),
                                        self,instance,"endOfTransmission"))
            newEvents.append(Event.Event(refTime+self.workload(instance.flow)+self.delay,
                                        self,instance,"endOfDelivery"))
        else:
            newEvents.append(Event.Event(refTime + self.localScheduler.nextOpportunity(),
                                        self,None,"TransmissionOpportunity"))
        return newEvents

    def management(self,event):
        newEvents = []
        if event.eventType == "Arrival":
            if isinstance(event.instance,Coms.Flow):
                if not isinstance(event.instance.task, Coms.TaskEventTriggered):
                    tempEvent = event.copy()
                    tempEvent.refTime = event.refTime + event.instance.task.period
                    newEvents.append(tempEvent)
                    event.instance = event.instance.generateMessage()
            self.arrived.append(event.instance)
        if event.eventType ==  "endOfTransmission":
            self.arrived.remove(event.instance)
            self.in_transmission = None
        if event.eventType == "endOfDelivery":
            self.channeling.remove(event.instance)
            nextLinks = event.instance.flow.nextLinks(self)
            for l in nextLinks:
                newEvents.append(Event.Event(event.refTime,l,event.instance.onNewLink(),"Arrival"))
            if nextLinks == []:
                nextFlow = event.instance.flow.findNextFlow(self)
                for nf in nextFlow:
                    nf.refreshData(event.instance.carriedData)
                    if isinstance(nf.task,Coms.TaskEventTriggered):
                        taskEvent = nf.task.istrigger(event)
                        if taskEvent:
                            newEvents.append(taskEvent)
        if event.eventType == "TransmissionOpportunity" and not self.in_transmission:
            newEvents += self.sendDecision(event.refTime)
        return newEvents


