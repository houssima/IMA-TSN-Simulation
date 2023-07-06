class Event:
    def __init__(self,refTime,link,instance,eventType):
        self.refTime = refTime
        self.link = link
        self.instance = instance
        self.eventType = eventType

    def __repr__(self) -> str:
        return self.eventType+" of {} on {} at {}\n".format(self.instance,self.link.id,self.refTime)

    def __str__(self) -> str:
        return self.eventType+" of {} on {} at {}\n".format(self.instance,self.link.id,self.refTime)

    def copy(self):
        return Event(self.refTime,self.link,self.instance,self.eventType)
        