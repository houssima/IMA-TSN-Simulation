from math import ceil
from pyclbr import Function
from re import L
import matplotlib.pyplot as plt
import matplotlib.patches as patches

import numpy as np
import myClasses.Communications as Communications
import myClasses.Event as Event
import myClasses.Link as Link

def runSimulation(nb_increments,net,coms):
    
    nextEvent = []
    pastEvent = []
    #next event is the list with the events, its composed of lists with 3 elements :
    #   - the time when the event occurs
    #   - the link concerned by the event
    #   - the message or task concerned by the event
    #   - the type of event : arrival,End of Transmission, End of Delivery
    #ToDo : create class event here
    refTime = 0
    #this is the reference time of the simulation, all event are stamped with time in this referential, whatever the time of the link is



    #################Initialise Periodic Flows Events#####################

    for FC in coms.FCList:
        for flow in FC.flowList:
                #The start of a flow is always on a unique link so only one arrival event occurs
                nextEvent.append(Event.Event(flow.task.offset, flow.flowTree[0], flow,'Arrival'))

    nextEvent.sort(key = lambda x: x.refTime)
    #################Running the simulation#####################
    
    while refTime < nb_increments:
    
        while nextEvent[0].refTime == refTime:
            #when an event occurs, we manage the link concerned by this event
            currEvent = nextEvent.pop(0)
            print(currEvent)
            newEvents = currEvent.link.management(currEvent)
            nextEvent+= newEvents         
            pastEvent.append(currEvent)
            nextEvent.sort(key = lambda x: (x.refTime, x.eventType))
            
        for l in net.links:
            if l.arrived and not l.in_transmission:
                nextEvent += l.sendDecision(refTime)
        nextEvent.sort(key = lambda x: (x.refTime, x.eventType))
        print(refTime,nextEvent)
        #Finally we sort the event in the future and go to the next event reference time
        timeShift = nextEvent[0].refTime - refTime
        refTime = nextEvent[0].refTime


        net.timeUpdate(timeShift)
    

    ##############Analyze results   ############################

    LatenciesNames = []
    tempLatencies = []
    for FC in coms.FCList:
        InitFlows = FC.findInitFlows()
        TermFlows = FC.findTermFlows()
        Latencies = [[[] for k in range(len(TermFlows))] for l in range(len(InitFlows))]

        chainInput = []
        for f_init in InitFlows:
            root = f_init.flowTree[0]
            for e in pastEvent:
                if isinstance(e.instance,Communications.FlowInstance):
                    if e.eventType == "Arrival" and e.instance.flow == f_init and e.link ==root:
                        chainInput.append(e)
        
        chainOutput = []
        for f_out in TermFlows:
            for l in f_out.flowTree:
                isLeaf = True
                for l1 in f_out.flowTree:
                    if l1 != l and l1.src == l.dst:
                        isLeaf = False
                if isLeaf:
                    for e in pastEvent:
                        if e.eventType == "endOfDelivery" and e.instance.flow == f_out and e.link == l:
                            chainOutput.append(e)
        for eventOut in chainOutput:
            for e in chainInput:
                for d in e.instance.carriedData:
                    for dO in eventOut.instance.carriedData:
                        if d.instanceNumber == dO.instanceNumber and d.data == dO.data: 
                            Latencies[InitFlows.index(e.instance.flow)][TermFlows.index(eventOut.instance.flow)].append(eventOut.refTime - e.refTime)
        
        for i in range(len(InitFlows)):
            for t in range(len(TermFlows)):
                tempLatencies.append(Latencies[i][t])
                LatenciesNames.append('from $f_'+str(InitFlows[i].id)+'$ to $f_{'+str(TermFlows[t].id)+'}$')                
                # SortedLat = sorted(list(set(Latencies[i][t])))
                # HIST_BINS = []
                # LatShift = (SortedLat[-1] - SortedLat [0]) /(2*len(SortedLat))
                # for lat in SortedLat:
                #     HIST_BINS.append(lat-LatShift)
                #     HIST_BINS.append(lat+LatShift)
                # plt.figure()
                # plt.hist( Latencies[i][t], HIST_BINS,rwidth= 0.1)
                # plt.title('Functional delay distribution from $f_'+str(InitFlows[i].id)+'$ to $f_{'+str(TermFlows[t].id)+'}$')
                # plt.xlabel('delay(FC) (in ms)')
                # plt.ylabel('occurencies during simulation')
                # plt.show()
       
        
        FunctionPath = [] 
        for f in FC.flowList:
            for link in f.flowTree:
                if link not in FunctionPath:
                    FunctionPath.append(link)
        
        fig2, ax = plt.subplots((len(FunctionPath))*3, sharex=True)

        for curLink in FunctionPath:
            linkPos = FunctionPath.index(curLink)
            ax[linkPos*3].set_ylabel('$'+'arr_{L_{'+str(curLink.id)+'}}'+'$',rotation = 0,fontsize =18,usetex = True)
            ax[linkPos*3].yaxis.set_label_coords(-.1, .0)
            ax[linkPos*3+1].set_ylabel('$'+'trans_{L_{'+str(curLink.id)+'}}'+'$',rotation = 0,fontsize =18,usetex = True)
            ax[linkPos*3+1].yaxis.set_label_coords(-.1, .0)
            ax[linkPos*3+2].set_ylabel('$'+'del_{L_{'+str(curLink.id)+'}}'+'$',rotation = 0,fontsize =18,usetex = True)
            ax[linkPos*3+2].yaxis.set_label_coords(-.1, .0)
            for i in range(3):
                 ax[linkPos*3+i].plot(np.linspace(0,nb_increments,100),np.zeros((100,1)),'--k')
            for event in pastEvent:
                if isinstance(event.instance,Communications.FlowInstance) and event.link == curLink:
                    if event.eventType == 'Arrival' and isinstance(event.instance,Communications.FlowInstance):
                        
                        for e2 in pastEvent:
                            if e2.eventType == 'Transmission' and e2.instance.flow == event.instance.flow and e2.instance.instanceNumber == event.instance.instanceNumber and e2.link == curLink:
                                endEvent = e2
                                break
                        if endEvent.refTime != event.refTime:
                            ax[linkPos*3].add_patch(patches.Rectangle((event.refTime,0),endEvent.refTime-event.refTime,1,facecolor = event.instance.flow.color))
                        else:
                            ax[linkPos*3].add_patch(patches.Ellipse((event.refTime,0.5), 0.25*nb_increments/len(FunctionPath),0.5,facecolor = event.instance.flow.color))
                    if event.eventType =='Transmission':
                        ax[linkPos*3+1].add_patch(patches.Rectangle((event.refTime,0),curLink.workload(event.instance.flow),1,facecolor = event.instance.flow.color))
                    if event.eventType == 'Delivery':
                        ax[linkPos*3+2].add_patch(patches.Rectangle((event.refTime,0),curLink.workload(event.instance.flow),1,facecolor = event.instance.flow.color))
        legendElements = []
        for f in FC.flowList:
            legendElements.append(patches.Patch(facecolor = f.color, label = '$'+'flow_{'+str(f.id)+'}'+'$'))
        ax[0].legend(handles = legendElements, loc='upper right', bbox_to_anchor=(1.12, 0.5))
        plt.xlabel('time (in microseconds)')
        plt.show()
    

    return tempLatencies, LatenciesNames
    # fig1 = plt.figure()
    # plt.boxplot(tempLatencies,
    #     labels=LatenciesNames)
    # plt.title('Functional delays distribution comparision')
    # plt.xlabel('Data start and end points')
    # plt.ylabel('delay(FC) (in ms)')
    # plt.show()



        
