class Node:
    def __init__(self,id,net,drift = 1, offset = 0, proc = 0):
        self.currentTime = offset
        self.drift = drift
        self.proc = proc
        self.ToTimeUpdate = True
        self.id = id
        self.PTP_Profile = None #Slave/Master/Boundary
        net.Elements.append(self)

    def timeUpdate(self, timeshift):
        self.currentTime = timeshift*self.drift + self.currentTime

    def synchronisation(self, Time):
        self.currentTime = Time
    
    def reset(self, offset = 0):
        self.currentTime = offset