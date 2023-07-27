import numpy as np

class GlobalSched:
    def __init__(self):
        self.StrategyList = []

    def findStrat(self,link):
        found = False
        i=0
        while not found:
            if self.StrategyList[i].link == link:
                return self.StrategyList[i]
            i+=1

class SchedStrategy:
    def __init__(self,link, globalSched):
        globalSched.StrategyList.append(self)
        self.array = None
        self.link = link
        link.localScheduler = self
    
    def shapeMatrix(self, shape = (8,3)):
        self.array = np.array([[None for i in range(shape[1])] for j in range(shape[0])])

    def autoComplete(self):
        for prio in range(self.array.shape[0]):
            for order in range(self.array.shape[1]-1):
                if not self.array[prio,order]:
                    self.array[prio,order] = FIFO(self.link,prio)
                    self.array[prio,order].findPrev(self.array)

        if np.all(self.array[:,-1] == None):
            mySPQ = SPQ(self.link)
            for i in range(self.array.shape[0]):
                self.array[i,-1]= mySPQ
            mySPQ.findPrev(self.array)

    def nextOpportunity(self):
        polTimes = []
        usedQueues= set([self.link.prio(m.flow)for m in self.link.arrived])
        for i in range(self.array.shape[1]):
            for j in usedQueues:
                if self.array[j,i].delayingPolicy:
                    polTimes.append(self.array[j,i].nextOpportunity())
        return min(polTimes)

    def electMessage(self):
        listElected = []
        for i in range(self.array.shape[1]):
            for pol in self.array[:,i]:
                pol.refreshState()
        for instance in self.link.arrived:                                               #Ce traitement ne correspond pas au modèle mais permet
            if self.array[self.link.prio(instance.flow),0].rule(instance) ==1:           #de réduire le temps de calcul (idem pour la variable "state" de Policy)
                    listElected.append(instance)                                         #On ne traite par la suite que les messages qui sont éligible selon les précédentes politiques
        for i in range(1,self.array.shape[1]):
            toRemove = listElected.copy()
            for instance in listElected:
                a = self.array[self.link.prio(instance.flow),i].rule(instance)
                if a == 0:
                    toRemove.remove(instance)
            listElected = toRemove
        if self.array[0,-1].instanceElected: return(self.array[0,-1].instanceElected[0])
        else: return None

class Policy:
    def __init__(self,prio,order,link,globalSched):
        globalSched.findStrat(link).array[prio,order] = self
        self.state = 1
        self.instanceElected = []
        self.delayingPolicy = False
        self.link = link
        self.prio = prio
        self.order = order

    def refreshState(self):
        self.state = 1
        self.instanceElected = []
    
    def findPlace(self,polArray):
        places = []
        for prio in range(polArray.shape[0]):
            for order in range(polArray.shape[1]):
                if polArray[prio,order] == self:
                    places.append((prio,order))
        return places

    def getQueue(self, instance):
        if self.link.linkType == "CPU":
            return instance.flow.task.prio
        if self.link.linkType == "DMA":
            return 0
        else:
            return instance.flow.message.prio



class FIFO(Policy):
    def __init__(self,prio,order,link,globalSched):
        Policy.__init__(self,prio,order,link,globalSched)
        self.previousPolicy=None
        
        
        
    def findPrev(self,polArray):
        places = self.findPlace(polArray)
        for place in places:
            if place[1] != 0:
                self.previousPolicy = polArray[place[0],place[1]-1]

    def rule(self,instance):
        if self.state ==1 :
            if self.previousPolicy:
                compareTo = [self.previousPolicy.messageElected]
            else:
                compareTo = self.link.arrived
            for m in compareTo:
                if self.getQueue(m) == self.prio:
                    if instance.time_since_arrival< m.time_since_arrival:
                        return 0
                    else:
                        self.state= 0
                        self.instanceElected.append(instance)
                        return 1
        else: 
            return 0

class GCL(Policy):
    #Gate controlled list is a mechanism 
    def __init__(self,prio,order,link,globalSched):
        Policy.__init__(self,prio,order,link,globalSched)
        self.priority = prio
        self.windows = []
        self.period = 1
        self.delayingPolicy = True
        
    def rule(self,instance):
        if self.state == 1:
            #time is in ms
            #clock cycle is about ns
            # times can be rounded to 0.1ns, so 10e-7 in the simulator
            currentPhase = round(self.link.src.currentTime%self.period, 7)
            cond = False
            
            for w in self.windows:
                for k in range(int(self.period/w[2])):
                    if currentPhase >= w[0]+k*w[2] and w[1]+ w[0] +k*w[2]- currentPhase >= self.link.workload(instance.flow):
                        cond = True
                    if currentPhase- self.period >= w[0]+k*w[2] and w[1]+ w[0] +k*w[2]- (currentPhase - self.period)>= self.link.workload(instance.flow):
                        cond = True
            if cond:
                self.instanceElected.append(instance)
                return 1
            else:
                return 0
        else:
            return 0
    
    def addWindow(self,offset,length,period):
        self.windows.append([offset,length,period])
        if len(self.windows)>1:
            self.period = np.lcm(self.period,period)
            
        else:
            self.period = period

    def nextOpportunity(self):
        #time is in ms
        #clock cycle is about ns
        # times can be rounded to 0.1ns, so 10e-7 in the simulator
        currentPhase = round(self.link.src.currentTime%self.period, 7)
        opportunities = []
        for w in self.windows:
            for k in range(int(2*self.period/w[2])):
                meetTime = w[0]+k*w[2] - currentPhase
                if w[0]+k*w[2] - currentPhase > 0:
                    opportunities.append(meetTime)
        return min(opportunities)

class SPQ(Policy):
    def __init__(self,prio,order,link,globalSched):
        Policy.__init__(self,prio,order,link,globalSched)
        self.previousPolicies = []

    def findPrev(self):
        polArray = self.link.localScheduler.array
        places = self.findPlace(polArray)
        for place in places:
            self.previousPolicies.append(polArray[place[0],place[1]-1])
       
    def rule(self,instance):
        if self.state == 1:
            messages = []
            for pol in self.previousPolicies:
                for m in pol.instanceElected:
                    if self.getQueue(m) > self.getQueue(instance):
                        messages.append(m)
            if not messages:
                self.state = 0
                self.instanceElected.append(instance)
                return 1
        else: 
            return 0