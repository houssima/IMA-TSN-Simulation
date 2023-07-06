class Node:
    def __init__(self,id,net,drift = 1, offset = 0, proc = 0):
        self.currentTime = offset
        self.drift = drift
        self.proc = proc
        self.ToTimeUpdate = True
        self.id = id
        net.Elements.append(self)

    def timeUpdate(self, timeshift):
        self.currentTime = timeshift*self.drift + self.currentTime

    def synchronisation(self, refTime):
        self.currentTime = refTime

# class Switch:
#     def __init__(self,id,net,drift = 1, offset = 0, proc = 0):
#         Node.__init__(self,id,net,drift,offset,proc)

# class Module:
#     def __init__(self,id, net,drift = 1, offset = 0, proc = 0):
#         Node.__init__(self,id, net,drift,offset,proc)