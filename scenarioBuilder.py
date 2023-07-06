#######################################################################
# Copyright (C) 2022-2023, ONERA and ISAE, Toulouse, FRANCE
#
# This file is part of IMA-TSN-Simulator
#
# IMA-TSN-Simulator is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation ; either version 2 of
# the License, or (at your option) any later version.
#
# IMA-TSN-Simulator is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY ; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program ; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#######################################################################

import numpy as np
import myClasses.NetworkClasses2 as NC2
from myClasses.Policies import GlobalSched, Policy
import Simulator as SIM
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

def netBuilder(data):

    PHYNET = NC2.PhysicalNetwork('net')

    for n in data["nodes"]:
        NC2.Nodes.Node(n["id"],PHYNET,n['drift'],n['offset'])
        print(PHYNET.Elements[-1])

        
    for l in data["links"]:
        if  l['linkType'] == 'CPU':
            NC2.Link.Link( int(l['id']), PHYNET.findElement(NC2.Nodes.Node,l['sourceNode']), 
                            PHYNET.findElement(NC2.Nodes.Node,l['endNode']),
                            0,l['linkType'],PHYNET)
        elif l['linkType']=="Net":
            NC2.Link.Link(  int(l['id']),PHYNET.findElement(NC2.Nodes.Node,l['sourceNode']), 
                            PHYNET.findElement(NC2.Nodes.Node,l['endNode']),
                            float(l['rate']), l['linkType'],PHYNET,float(l["delay"]))
        elif l['linkType']=="DMA":
            NC2.Link.Link(  int(l['id']),PHYNET.findElement(NC2.Nodes.Node,l['sourceNode']), 
                            PHYNET.findElement(NC2.Nodes.Node,l['endNode']),
                            float(l['rate']), l['linkType'],PHYNET)
                            
    return PHYNET

def comBuilder(data,PHYNET):
    coms = NC2.Coms.Communications()

    for c in data["chains"]:
        curFC = NC2.Coms.FunctionnalChain(coms)
        curFC.PrecRelation = c['flowPrec']
        for flow in c['f_{in}']+c['f_{mid}']+c['f_{out}']:
            flowData = data["flows"][flow]
            taskData = data["tasks"][flowData["task"]]
            curTask = NC2.Coms.Task(taskData['T'],taskData['C'],
                                    taskData['T'],taskData['r'],
                                    taskData['prio'])
            mess = data["messages"][flowData['msg']]
            currMess = NC2.Coms.Message(mess['len'],mess['priority'])
            if flowData['dataManagement'] == 'sampling':
                currFlow = NC2.Coms.Flow(flowData["id"],curTask,currMess,curFC)
            elif flowData['dataManagement'] == 'queuing':
                currFlow = NC2.Coms.QueuingFlow(flowData["id"],curTask,currMess,curFC)
            currFlow.flowTree = [PHYNET.findElement(NC2.Link.Link, id) for id in flowData['flowTree']]
            
            for dataID in c['delta']:
                for d in data["data"]:
                    if d['sourceFlow']==flowData["id"]:
                        currFlow.dataEntry = NC2.Coms.Data(curFC,flow)
    return coms


def schedBuilder(data, PHYNET):

    GLOBALSCHED = NC2.Policies.GlobalSched()
    for sched in data["schedulingMatrixes"]:
        curLink = PHYNET.findElement(NC2.Link.Link,sched['link'])
        NC2.Policies.SchedStrategy(curLink,GLOBALSCHED)
        curLink.localScheduler.shapeMatrix(sched['size'])

    for p in data["Policies"]:
        if p['name'] == 'FIFO':
            placements = p['placements']
            for pla in placements:
                curLink = PHYNET.findElement(NC2.Link.Link,pla['link'])
                for place in pla['places']:
                    NC2.Policies.FIFO(place[0],place[1],curLink,GLOBALSCHED)
        elif p['name'] == 'GCL':
            placements = p['placements']
            for pla in placements:
                curLink = PHYNET.findElement(NC2.Link.Link,pla['link'])
                for place in pla['places']:                
                    GCL = NC2.Policies.GCL(place[0],place[2],curLink,GLOBALSCHED)
                    for prio in range(place[0],place[1]):
                        curLink.localScheduler.array[prio,place[2]] = GCL
                    for win in pla['windows']:
                        GCL.addWindow(win[0],win[1],win[2])
        elif p['name']== 'SPQ':
            placements = p['placements']
            for pla in placements:
                curLink = PHYNET.findElement(NC2.Link.Link,pla['link'])
                for place in pla['places']:
                    SPQ = NC2.Policies.SPQ(place[0],place[2],curLink,GLOBALSCHED)
                    for prio in range(place[0],place[1]):
                        curLink.localScheduler.array[prio,place[2]] = SPQ
                    SPQ.findPrev()
    


                
if __name__ == "__main__":
    conffile = "confs/FullGCL.json"
    with open(conffile) as user_file:
        file_contents = user_file.read()
    data = json.loads(file_contents)
    PHYNET = netBuilder(data)
    coms = comBuilder(data, PHYNET)
    schedBuilder(data,PHYNET)
    tempLatencies, LatenciesNames = SIM.runSimulation(32,PHYNET,coms)

    conffile = "confs/PartitionnedScenario.json"
    with open(conffile) as user_file:
        file_contents = user_file.read()
    data = json.loads(file_contents)
    PHYNET = netBuilder(data)
    coms = comBuilder(data, PHYNET)
    schedBuilder(data,PHYNET)
    tempLatencies1, LatenciesNames = SIM.runSimulation(32,PHYNET,coms)

    conffile = "confs/FullSPQScenario.json"
    with open(conffile) as user_file:
        file_contents = user_file.read()
    data = json.loads(file_contents)
    PHYNET = netBuilder(data)
    coms = comBuilder(data, PHYNET)
    schedBuilder(data,PHYNET)
    tempLatencies2, LatenciesNames = SIM.runSimulation(32,PHYNET,coms)



    boxData = [
        # The definition of the box size depends on the number of tests
        tempLatencies[0],   tempLatencies1[0],  tempLatencies2[0],
        tempLatencies[1],   tempLatencies1[1],  tempLatencies2[1],
        tempLatencies[2],   tempLatencies1[2],  tempLatencies2[2]
    ]


    fig, ax1 = plt.subplots(figsize=(10, 6))
    bp = ax1.boxplot(boxData)

    ax1.set(
    axisbelow=True,  # Hide the grid behind plot objects
    title   =   'Comparison functional delays distributions',
    xlabel  =   'Functional Chain',
    ylabel  =   'Delay (ms)',
)


    box_colors = ['darkkhaki', 'royalblue','red']
    num_boxes = len(boxData)
    medians = np.empty(num_boxes)
    for i in range(num_boxes):
        box = bp['boxes'][i]
        box_x = []
        box_y = []
        for j in range(5):
            box_x.append(box.get_xdata()[j])
            box_y.append(box.get_ydata()[j])
        box_coords = np.column_stack([box_x, box_y])
        # Alternate between Dark Khaki and Royal Blue
        ax1.add_patch(Polygon(box_coords, facecolor=box_colors[i % 3]))
        # Now draw the median lines back over what we just filled in
        med = bp['medians'][i]
        median_x = []
        median_y = []
        for j in range(2):
            median_x.append(med.get_xdata()[j])
            median_y.append(med.get_ydata()[j])
            ax1.plot(median_x, median_y, 'k')
        medians[i] = median_y[0]
        # Finally, overplot the sample averages, with horizontal alignment
        # in the center of each box
        ax1.plot(np.average(med.get_xdata()), np.average(boxData[i]),
                color='w', marker='#', markeredgecolor='k')

    ax1.set_xticklabels(np.repeat(LatenciesNames,3),
                    rotation=45, fontsize=14)
    pos = np.arange(num_boxes) + 1
    print([len(Latencies) for Latencies in boxData])
    upper_labels =  [ [round(min(Latencies),2),round(max(Latencies),2)] for Latencies in boxData]
    weights = ['bold', 'semibold']
    for tick, label in zip(range(num_boxes), ax1.get_xticklabels()):
        k = tick % 3
        ax1.text(pos[tick], .97, upper_labels[tick],
                transform=ax1.get_xaxis_transform(),
                horizontalalignment='center', size='x-small',
                weight='bold', color=box_colors[k])

    # Finally, add a basic legend
    fig.text(0.9, 0.1, 'GCL configuration',
            backgroundcolor=box_colors[0], color='black', weight='roman',
            size='x-small')
    fig.text(0.9, 0.07, 'Partitionned configuration',
            backgroundcolor=box_colors[1],
            color='white', weight='roman', size='x-small')
    fig.text(0.9, 0.04, 'SPQ configuration', color='white', backgroundcolor=box_colors[2],
            weight='roman', size='x-small')
    fig.text(0.915, 0.013, ' Average Value', color='black', weight='roman',
            size='x-small')
    plt.show()