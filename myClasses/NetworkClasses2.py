import myClasses.Communications as Coms
import myClasses.Link as Link
import myClasses.Nodes as Nodes
import myClasses.Policies as Policies



class PhysicalNetwork:
    def __init__(self,name):
        self.name = name
        self.nb_links = 0
        self.links = []
        self.Elements = []
        
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
        

            