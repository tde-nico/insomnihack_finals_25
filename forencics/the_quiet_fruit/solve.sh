#!/bin/bash

strings 'Results/C/$MFT' | grep "INS_"
# INS_PART2{N@ughTyS3rv!ce}

grep -r "SU5T"
Results/C/Program Files/KeePass Password Safe 2/KeePass.config.enforced.xml: <Parameter>SU5TX1BBUlQxe0tlM1BAcyRCYWNrRDAwcn0=</Parameter>
strings Results/C/Windows/System32/wbem/Repository/OBJECTS.DATA | grep SU5T
echo 'SU5TX1BBUlQxe0tlM1BAcyRCYWNrRDAwcn0=' | base64 -d
# INS_PART1{Ke3P@s$BackD00r}
echo 'SU5TX1BBUlQze1dNSV9BbHdheXNfRG9lc19UaGVfSm9ifQ' | base64 -d
# INS_PART3{WMI_Always_Does_The_Job}

# INS{INS_PART1{Ke3P@s$BackD00r}INS_PART2{N@ughTyS3rv!ce}INS_PART3{WMI_Always_Does_The_Job}}
