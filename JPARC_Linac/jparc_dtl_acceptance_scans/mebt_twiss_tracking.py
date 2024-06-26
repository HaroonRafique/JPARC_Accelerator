#! /usr/bin/env python

"""
This script will track the bunch through the MEBT of the JPARC Linac.
The apertures are added to the lattice.
"""

import sys
import math
import random
import time

from orbit.py_linac.linac_parsers import JPARC_LinacLatticeFactory

# from linac import the C++ RF gap classes
from linac import BaseRfGap, MatrixRfGap, RfGapTTF

from orbit.bunch_generators import TwissContainer
from orbit.bunch_generators import WaterBagDist3D, GaussDist3D, KVDist3D

from bunch import Bunch
from bunch import BunchTwissAnalysis

from orbit.lattice import AccLattice, AccNode, AccActionsContainer

from orbit.py_linac.lattice_modifications import Add_quad_apertures_to_lattice
from orbit.py_linac.lattice_modifications import Add_rfgap_apertures_to_lattice

from orbit.py_linac.lattice_modifications import Replace_BaseRF_Gap_to_AxisField_Nodes
from orbit.py_linac.lattice_modifications import Replace_BaseRF_Gap_and_Quads_to_Overlapping_Nodes
from orbit.py_linac.lattice_modifications import Replace_Quads_to_OverlappingQuads_Nodes

from orbit.py_linac.overlapping_fields import JPARC_EngeFunctionFactory

from jparc_linac_bunch_generator import JPARC_Linac_BunchGenerator

random.seed(100)


#---- Define the list of subsequences for the lattice
names = ["LI_MEBT1",]

#---- create the factory instance
jparc_linac_factory = JPARC_LinacLatticeFactory()
jparc_linac_factory.setMaxDriftLength(0.01)

#---- the XML file name with the structure
xml_file_name = "../jparc_linac_lattice_xml/jparc_linac.xml"

#---- make lattice from XML file 
accLattice = jparc_linac_factory.getLinacAccLattice(names,xml_file_name)

seq_names = names

print "Linac lattice is ready. L=",accLattice.getLength()

#----set up RF Gap Model -------------
#---- There are three available models at this moment
#---- BaseRfGap  uses only E0TL*cos(phi)*J0(kr) with E0TL = const
#---- MatrixRfGap uses a matrix approach like envelope codes
#---- RfGapTTF uses Transit Time Factors (TTF) like PARMILA
cppGapModel = BaseRfGap
#cppGapModel = MatrixRfGap
#cppGapModel = RfGapTTF
rf_gaps = accLattice.getRF_Gaps()
for rf_gap in rf_gaps:
	rf_gap.setCppGapModel(cppGapModel())

#----- the LI_MEBT1:BNCH01 and LI_MEBT1:BNCH02 have different E0TL in the Trace3D
#----- file (see ./optics/jparc_matched2_40mA100_trace3d_rfgaps.dat file)
rf_gaps[0].setParam("E0TL",0.135408/1000.)
rf_gaps[2].setParam("E0TL",0.147204/1000.)

node_pos_dict = accLattice.getNodePositionsDict()

#----- Read quads from the external file and set the lattice quads' fields accordingly
quad_fl_in = open("./optics/jparc_matched2_40mA100_trace3d_quads.dat","r")
lns = quad_fl_in.readlines()[1:]
quad_fl_in.close()
quad_names_field_dict = {}
for ln in lns:
	res_arr = ln.split()
	if(len(res_arr) > 2):
		name = res_arr[0].strip()
		field = float(res_arr[1])
		quad_names_field_dict[name] = field
		#print "debug trace3d quad =",name," field=",field

quads = accLattice.getQuads()
for quad in quads:
	if(quad_names_field_dict.has_key(quad.getName())):
		field = quad_names_field_dict[quad.getName()]
		quad.setParam("dB/dr",field)
		#print "debug quad =",quad.getName()," G=",quad.getParam("dB/dr")

#----- Print out quads fields and positions ==================  START
quads = accLattice.getQuads()
quad_fl_out = open("quad_params.dat","w")
quad_fl_out.write(" Quad  G[T/m]   length[m]   pos[m]    \n")
for quad in quads:
	[pos_start,pos_end] = node_pos_dict[quad]
	pos = (pos_start+pos_end)/2
	length = quad.getLength()
	field = quad.getParam("dB/dr")
	quad_fl_out.write(quad.getName()+ "  %+10.6f"%field+"  %+10.6f"%length  + "  %+12.6f"%pos  +"\n" )
quad_fl_out.close()
#----- Print out quads fields and positions ==================  END

#------------------------------------------------------------------
#---- Hard edge quads will be replaced by distributed fields for specified sequences 
#------------------------------------------------------------------
#---- longitudinal step along the distributed fields lattice
z_step = 0.001

Replace_Quads_to_OverlappingQuads_Nodes(accLattice,z_step,["LI_MEBT1",],[],JPARC_EngeFunctionFactory)
#Replace_Quads_to_OverlappingQuads_Nodes(accLattice,z_step,["LI_MEBT1","LI_DTL1"],[],JPARC_EngeFunctionFactory)
#Replace_Quads_to_OverlappingQuads_Nodes(accLattice,z_step,seq_names,[],JPARC_EngeFunctionFactory)
print "Linac new lattice is ready. L=",accLattice.getLength()
#-----------------------------------------------------
# Set up Space Charge Acc Nodes
#-----------------------------------------------------
from orbit.space_charge.sc3d import setSC3DAccNodes, setUniformEllipsesSCAccNodes
from spacecharge import SpaceChargeCalcUnifEllipse, SpaceChargeCalc3D
sc_path_length_min = 0.003

print "Set up Space Charge nodes. "

# set of uniformly charged ellipses Space Charge
nEllipses = 1
calcUnifEllips = SpaceChargeCalcUnifEllipse(nEllipses)
space_charge_nodes = setUniformEllipsesSCAccNodes(accLattice,sc_path_length_min,calcUnifEllips)

"""
# set FFT 3D Space Charge
sizeX = 64
sizeY = 64
sizeZ = 64
calc3d = SpaceChargeCalc3D(sizeX,sizeY,sizeZ)
space_charge_nodes =  setSC3DAccNodes(accLattice,sc_path_length_min,calc3d)
"""

max_sc_length = 0.
min_sc_length = accLattice.getLength()
for sc_node in space_charge_nodes:
	scL = sc_node.getLengthOfSC()
	if(scL > max_sc_length): max_sc_length = scL
	if(scL < min_sc_length): min_sc_length = scL
print "maximal SC length =",max_sc_length,"  min=",min_sc_length

print "===== Aperture Nodes START  ======="
aprtNodes = Add_quad_apertures_to_lattice(accLattice)
aprtNodes = Add_rfgap_apertures_to_lattice(accLattice,aprtNodes)

"""
for node in aprtNodes:
	print "aprt=",node.getName()," pos =",node.getPosition()
"""

print "===== Aperture Nodes Added ======="

#-----TWISS Parameters at the entrance of MEBT1 ---------------
# transverse emittances are unnormalized and in pi*mm*mrad
# longitudinal emittance is in pi*eV*sec
e_kin_ini = 0.003 # in [GeV]
mass = 0.939294    # in [GeV]
gamma = (mass + e_kin_ini)/mass
beta = math.sqrt(gamma*gamma - 1.0)/gamma
print "relat. gamma=",gamma
print "relat.  beta=",beta
frequency = 324.0e+6
v_light = 2.99792458e+8  # in [m/sec]

#-----------------------------------------------------------------
#------ Twiss parameters from Trace3D 
#------ x,x'  y,y'  mm,mrad 
#------ Long Twiss: emittance deg*keV , beta deg/keV 
#------ All emittances are 5 times bigger the RMS values
#------ The Trace3D file is 
#------ ../jparc_linac_xml_generator/jparc_trace3d_lattice/jparc_matched2_40mA100.t3d

(alphaX,betaX,emittX) =  (-2.153,   0.18313, (13.4606/5)*1.0E-6)
(alphaY,betaY,emittY) =  ( 1.8253,  0.15578, (13.3520/5)*1.0E-6)
(alphaZ,betaZ,emittZ) =  (-0.08328, 0.91909, (538.69/5))

"""
 From Trace3D input file ()
 === for 40 mA =====
 ER= 939.3014, Q= -1.0, W =  3.0, XI=  50.0,XI=15,XI=40
 EMITI =     13.460568358239064 13.352006807621624 538.68785
 BEAMI =    -2.153	.18313	1.8253	.15578	-.08328	.9190900000000001

"""
#---- Translate long. Twiss from Trace3D to PyORBIT (emittance m*GeV , beta m/GeV)
betaZ  = betaZ *(v_light*beta/(360.*frequency))*1.0E+6
emittZ = emittZ*(v_light*beta/(360.*frequency))/1.0E+6

print " ========= PyORBIT Twiss ==========="
print " aplha beta emitt[mm*mrad] X= %6.4f %6.4f %6.4f "%(alphaX,betaX,emittX*1.0e+6)
print " aplha beta emitt[mm*mrad] Y= %6.4f %6.4f %6.4f "%(alphaY,betaY,emittY*1.0e+6)
print " aplha beta emitt[mm*MeV] Z= %6.4f %6.4f %6.4f "%(alphaZ,betaZ,emittZ*1.0e+6)

twissX = TwissContainer(alphaX,betaX,emittX)
twissY = TwissContainer(alphaY,betaY,emittY)
twissZ = TwissContainer(alphaZ,betaZ,emittZ)

print "Start Bunch Generation."
bunch_gen = JPARC_Linac_BunchGenerator(twissX,twissY,twissZ)

#set the initial kinetic energy in GeV
bunch_gen.setKinEnergy(e_kin_ini)

#set the beam peak current in mA
bunch_gen.setBeamCurrent(40.0)

#bunch_in = bunch_gen.getBunch(nParticles = 10000, distributorClass = WaterBagDist3D)
bunch_in = bunch_gen.getBunch(nParticles = 100000, distributorClass = GaussDist3D)
#bunch_in = bunch_gen.getBunch(nParticles = 10000, distributorClass = KVDist3D)

print "Bunch Generation completed."

#set up design - arrival times at each fist gaps of all RF cavities
accLattice.trackDesignBunch(bunch_in)

print "Design tracking completed."

#prepare to track through the lattice 
paramsDict = {"old_pos":-1.,"count":0,"pos_step":0.01}
actionContainer = AccActionsContainer("Test Design Bunch Tracking")

pos_start = 0.

twiss_analysis = BunchTwissAnalysis()

file_out = open("pyorbit_twiss_sizes_ekin.dat","w")

s = " Node   position "
s += "   alphaX betaX emittX  normEmittX"
s += "   alphaY betaY emittY  normEmittY"
s += "   alphaZ betaZ emittZ  emittZphiMeV"
s += "   sizeX sizeY sizeZ_deg"
s += "   eKin Nparts "
file_out.write(s+"\n")
#file_out.write("pos sizeX sizeY sizeZdeg \n")
print " N node   position    sizeX  sizeY  sizeZdeg  eKin Nparts "

#---- Here we define action that will analyze and print out beam parameters
#---- at the entrance and exit of each accelerator element (parents and children)

def action_entrance(paramsDict):
	node = paramsDict["node"]
	bunch = paramsDict["bunch"]
	pos = paramsDict["path_length"]
	if(paramsDict["old_pos"] == pos): return
	if(paramsDict["old_pos"] + paramsDict["pos_step"] > pos): return
	paramsDict["old_pos"] = pos
	paramsDict["count"] += 1
	gamma = bunch.getSyncParticle().gamma()
	beta = bunch.getSyncParticle().beta()
	twiss_analysis.analyzeBunch(bunch)
	x_rms = math.sqrt(twiss_analysis.getTwiss(0)[1]*twiss_analysis.getTwiss(0)[3])*1000.
	y_rms = math.sqrt(twiss_analysis.getTwiss(1)[1]*twiss_analysis.getTwiss(1)[3])*1000.
	z_rms = math.sqrt(twiss_analysis.getTwiss(2)[1]*twiss_analysis.getTwiss(2)[3])*1000.
	z_to_phase_coeff = bunch_gen.getZtoPhaseCoeff(bunch)
	z_rms_deg = z_to_phase_coeff*z_rms/1000.0
	nParts = bunch.getSizeGlobal()
	(alphaX,betaX,emittX) = (twiss_analysis.getTwiss(0)[0],twiss_analysis.getTwiss(0)[1],twiss_analysis.getTwiss(0)[3]*1.0e+6)
	(alphaY,betaY,emittY) = (twiss_analysis.getTwiss(1)[0],twiss_analysis.getTwiss(1)[1],twiss_analysis.getTwiss(1)[3]*1.0e+6)
	(alphaZ,betaZ,emittZ) = (twiss_analysis.getTwiss(2)[0],twiss_analysis.getTwiss(2)[1],twiss_analysis.getTwiss(2)[3]*1.0e+6)		 
	norm_emittX = emittX*gamma*beta
	norm_emittY = emittY*gamma*beta
	#---- phi_de_emittZ will be in [pi*deg*MeV]
	phi_de_emittZ = z_to_phase_coeff*emittZ	
	eKin = bunch.getSyncParticle().kinEnergy()*1.0e+3
	s = " %45s  %4.5f "%(node.getName(),pos+pos_start)
	s += "   %+6.4f  %+6.4f  %+6.4f  %+6.4f   "%(alphaX,betaX,emittX,norm_emittX)
	s += "   %+6.4f  %+6.4f  %+6.4f  %+6.4f   "%(alphaY,betaY,emittY,norm_emittY)
	s += "   %+6.4f  %+6.4f  %+6.4f  %+6.4f   "%(alphaZ,betaZ,emittZ,phi_de_emittZ)
	s += "   %5.3f  %5.3f  %5.3f "%(x_rms,y_rms,z_rms_deg)
	s += "  %10.6f   %8d "%(eKin,nParts)
	file_out.write(s +"\n")
	file_out.flush()
	#s_samll =  "%4.5f "%(pos+pos_start)+"  %5.3f  %5.3f   %5.3f "%(x_rms,y_rms,z_rms_deg)
	#file_out.write(s_samll +"\n")
	s_prt = " %5d  %35s  %4.5f "%(paramsDict["count"],node.getName(),pos+pos_start)
	s_prt += "  %5.3f  %5.3f   %5.3f "%(x_rms,y_rms,z_rms_deg)
	s_prt += "  %10.6f   %8d "%(eKin,nParts)
	print s_prt	
	
def action_exit(paramsDict):
	action_entrance(paramsDict)
	
actionContainer.addAction(action_entrance, AccActionsContainer.ENTRANCE)
actionContainer.addAction(action_exit, AccActionsContainer.EXIT)

#---- This is actual tracking of the bunch
time_start = time.clock()

accLattice.trackBunch(bunch_in, paramsDict = paramsDict, actionContainer = actionContainer)

time_exec = time.clock() - time_start
print "time[sec]=",time_exec

file_out.close()

