# Meraki Bulk Delete Guest Users

## Description

Python script designed for removing bulk Cisco Meraki guest users. You can add domains to ignore and set x number of days old to delete.

## Installation

### Prerequisites

- Python 3.8+
- Cisco Meraki Dashboard with an API key.

### Setup

1. Ensure Python 3.8 or higher is installed on your system.

2. Clone the repository or download `app.py`:

   ```
   git clone
   ```

   or download `app.py` directly.

3. Setup project

   - In terminal, navigate to the directory of the app
   - Run the following command to create a new virtual environment

   ```
   python3 -m venv env
   ```

   - Activate the environment

   ```
   source env/bin/activate
   ```

4. Install the `meraki` Python package:

   ```
   pip install meraki
   ```

5. Add your excluded domains and set the older than days parameter in the app.py file.

   ```python
   #----------------------------------------------------------------------------#
   # Variables
   #----------------------------------------------------------------------------#

   excluded_domains = [
       '@cisco.com',
       '@meraki.net'
   ]

   older_than_days = 30
   ```

6. REQUIRED! Must edit the `deleteNetworkMerakiAuthUser` from the Python SDK (hopefully this will be resolved in the future).

   Edit file `lib > python3.X > site-packages > meraki > api > networks.py`
   Search for `deleteNetworkMerakiAuthUser`
   Add `?delete=true` to the end of the resource. Or simply replace the entire function deleteNetworkMerakiAuthUser with the below:

   ```python
   def deleteNetworkMerakiAuthUser(self, networkId: str, merakiAuthUserId: str, **kwargs):
       """
       **Delete an 802.1X RADIUS user, or deauthorize and optionally delete a splash guest or client VPN user.**
       https://developer.cisco.com/meraki/api-v1/#!delete-network-meraki-auth-user

       - networkId (string): Network ID
       - merakiAuthUserId (string): Meraki auth user ID
       - delete (boolean): If the ID supplied is for a splash guest or client VPN user, and that user is not authorized for any other networks in the organization, then also delete the user. 802.1X RADIUS users are always deleted regardless of this optional attribute.
       """

       kwargs.update(locals())

       metadata = {
           'tags': ['networks', 'configure', 'merakiAuthUsers'],
           'operation': 'deleteNetworkMerakiAuthUser'
       }
       networkId = urllib.parse.quote(str(networkId), safe='')
       merakiAuthUserId = urllib.parse.quote(str(merakiAuthUserId), safe='')
       resource = f'/networks/{networkId}/merakiAuthUsers/{merakiAuthUserId}?delete=true'

       return self._session.delete(metadata, resource)
   ```

## Usage

To run the script, use the following command in the terminal:

```
python app.py
```

### Configuration

Before running the script, ensure that you have a Cisco Meraki API key. The script will prompt for this key if it's not found in your environment variables. Optionally, you can set the API key as an environment variable:

```
export MERAKI_DASHBOARD_API_KEY='your_api_key_here'
```

## Features

- Retrieve and list organizations and networks associated with the Meraki API key.
- Interactive selection of organizations and networks for further actions.
- Filtering guest users based on account type, domain, and account creation date.
- Capability to delete filtered guest users from selected networks.
- Error handling and logging for API interactions.

## Additional Notes

- The script does not permanently store any sensitive information like API keys or user data.
- Ensure that you have the necessary permissions on the Meraki Dashboard before performing deletions or other modifications.
- This script is intended for administrators with knowledge of the Meraki platform and Python scripting.
