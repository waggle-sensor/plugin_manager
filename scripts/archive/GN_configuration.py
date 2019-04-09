# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
"""
    This file stores all of the configurable variables for a guest node. 

"""



with open('/etc/waggle/hostname','r') as file_:
    HOSTNAME = file_.read().strip()
    
#gets the IP address for the nodecontroller
with open('/etc/waggle/NCIP','r') as file_:
    NCIP = file_.read().strip() 

#Unique ID for the nodecontroller
with open('/etc/waggle/NCID','r') as file_:
    NC_ID = file_.read().strip() 
