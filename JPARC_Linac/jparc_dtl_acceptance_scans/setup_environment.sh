# script to setup the PyOrbit environment 
# execute like: . setup_environment.sh

# HR Laptop local CERN PTC original
pyOrbit_dir=/home/HR/Codes/PTC_PyORBIT/Local_Test4/py-orbit_20210406

# Latest Merged PyORBIT: Merged HR PyORBIT + newPTC
#pyOrbit_dir=/apps20/contrib/ptc-pyorbit/PTC-PyORBIT/Merged_HR_PyORBIT_2/py-orbit

# Merged PTC: CERN PyORBIT + new PTC
#pyOrbit_dir=/apps20/contrib/ptc-pyorbit/PTC-PyORBIT/Merged_PTC_Test/py-orbit

# Merged PTC: HR (clone of CERN) PyORBIT + new PTC
#pyOrbit_dir=/apps20/contrib/ptc-pyorbit/PTC-PyORBIT/Merged_PTC/py-orbit

# Original CERN PyORBIT + old PTC
#~ pyOrbit_dir=/apps20/contrib/ptc-pyorbit/PTC-PyORBIT/CERN_PTC-PyORBIT/py-orbit

# local
source ${pyOrbit_dir}/../venv/bin/activate
# scarf
#~ source ${pyOrbit_dir}/../virtualenvs/py2.7/bin/activate
echo "python packages charged"
source ${pyOrbit_dir}/customEnvironment.sh
echo "customEnvironment done"
which python

ORBIT_ROOT_fullpath=`readlink -f ${ORBIT_ROOT}` 
echo 
echo "*****************************************************"
echo 
echo "full PyOrbit path:  ${ORBIT_ROOT_fullpath}"
echo
. ${ORBIT_ROOT}/../CheckGitStatus.sh ${ORBIT_ROOT_fullpath}

# Test: remove creation of bytecode to avoid race condition bug
export PYTHONDONTWRITEBYTECODE=1
