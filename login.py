#
# (C) Cisco Systems Inc.
# Maintened by Ivan Villalobos ivillalo@cisco.com
# Can be used and modified freely
#

# Helper Module to Authenticate through Uniq
 
import requests.exceptions

from config import APIC, APIC_USER, APIC_PASSWORD
from uniq.apis.nb.client_manager import NbClientManager

def login():
    
    # Returns: "client" structure once logged in

    try:
        client = NbClientManager( server=APIC, username=APIC_USER, password=APIC_PASSWORD, connect=True )
    except requests.exceptions.HTTPError as exc_info:
        if exc_info.response.status_code == 401:
            print( 'Authentication Failed. Please provide valid username/password.' )

        else:
            print('HTTP Status Code {code_samples}. Reason: {reason}'.format( code=exc_info.response.status_code, reason=exc_info.response.reason ) )
        exit( 1 )
    except requests.exceptions.ConnectionError:
        print( 'Connection aborted. Please check if the host {} is available.'.format( host ) )
        exit( 1 )

    return client
