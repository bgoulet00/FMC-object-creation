# FMC-object-creation
create network, range and host objects in bulk on cisco FMC

this script will create FMC host, range and network objects in bulk
the input file will be a csv in the format name,description,oject-type,value
the input file will have a header row with those descriptions which will be stripped off when the file is read
see the sample csv file for reference

BASE_URL needs to be updated with the FMC url/ip

written with python3.6.8 and tested on FMCv7.0.4
