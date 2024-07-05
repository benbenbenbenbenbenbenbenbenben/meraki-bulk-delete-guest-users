#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import meraki
import os
import getpass
import secrets
import datetime

#----------------------------------------------------------------------------#
# Variables
#----------------------------------------------------------------------------#

excluded_domains = [
    # '@cisco.com',
    # '@meraki.net'
]

older_than_days = 0

simulate_api_calls = False

#----------------------------------------------------------------------------#
# Meraki Object
#----------------------------------------------------------------------------#

def get_meraki_dashboard():
    if 'MERAKI_DASHBOARD_API_KEY' in os.environ:
        api_key = os.environ['MERAKI_DASHBOARD_API_KEY']
    else:
        api_key = getpass.getpass("Enter your Meraki API key: ")

    # Initialize the Meraki Dashboard object
    dashboard = meraki.DashboardAPI(
        api_key=api_key,
        base_url='https://api.meraki.com/api/v1/',
        output_log=False,
        print_console=False,
        simulate=simulate_api_calls
    )
    return dashboard

#----------------------------------------------------------------------------#
# App Config
#----------------------------------------------------------------------------#

m = get_meraki_dashboard()

#----------------------------------------------------------------------------#
# Functions
#----------------------------------------------------------------------------#

def display_list(list, title):
    # Creates a CLI list with given name and id
    print(f"{title}:")
    for idx, list in enumerate(list, start=1):
        print(f"{idx}. {list['name']} (ID: {list['id']})")


def get_user_selection(organizations):
    while True:
        try:
            selection = int(input("Enter the number corresponding to the organization you want to select: "))
            if 1 <= selection <= len(organizations):
                return organizations[selection - 1]['id'], organizations[selection - 1]['name']
            else:
                print("Invalid selection. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_user_org_selection():
    orgs = get_organisations()

    if not orgs:
        print("No organizations found.")
        return False

    sorted_orgs = sorted(orgs, key=lambda x: x['name'])
    display_list(sorted_orgs, 'Organizations')
    
    selected_org_id, org_name = get_user_selection(sorted_orgs)

    print(f"\nSelected Organization: {org_name} - {selected_org_id}")

    return selected_org_id

def get_user_function():
    print("1. Delete guest accounts older than specified days")
    print("2. Custom - Delete Unscoped users via CSV Upload")

    while True:
        try:
            selection = int(input("Select a function to run."))
            if selection == 1:
                return 1

            elif selection == 2:
                return 2
            else:
                print("Invalid selection. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

            
def filter_guests(users, account_type):
    filtered_guests = [user for user in users if user['accountType'].lower() == account_type]
    return filtered_guests

def filter_emails(users, excluded_domains):
    filtered_emails = [user for user in users if not any(user['email'].endswith(domain) for domain in excluded_domains)]
    return filtered_emails

def filter_dates(users, older_than_days):
    # Get the current date and time
    today = datetime.datetime.utcnow()

    # Calculate the date x days ago
    x_days_ago = today - datetime.timedelta(days=older_than_days)

    # Format the date in ISO 8601
    check_date = x_days_ago.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    filtered_dates = [user for user in users if not user['createdAt'] > check_date]

    return filtered_dates

def user_wants_to_continue():
    while True:
        user_input = input("Do you want to continue? (y/n): ").lower()
        if user_input == 'y':
            return True
        elif user_input == 'n':
            exit()
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

def create_user(email, description, networkId):
    today = datetime.datetime.now() + datetime.timedelta(minutes=5)
    expires = today.isoformat()
    return m.networks.createNetworkMerakiAuthUser(
        networkId,
        email=email,
        name=description,
        accountType="Guest",
        password=(''.join(secrets.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_-+=<>?") for _ in range(12))),
        authorizations = [
            {
                "ssidNumber": 0,
                "expiresAt": expires
            }
        ]
    )
        

#----------------------------------------------------------------------------#
# MERAKI APIs
#----------------------------------------------------------------------------#

# Get Organisations
def get_organisations():
    try:
        orgs = m.organizations.getOrganizations()
        return orgs
    except meraki.APIError as e:
        print(f'Meraki API error: {e}')
        print(f'status code = {e.status}')
        print(f'reason = {e.reason}')
        print(f'error = {e.message}')
        return {
            'message':e.message,
            'error':e.status
        }, e.status
    except Exception as e:
        print(f'some other error: {e}')

# Get Networks
def get_networks(orgId):
    try:
        networks = m.organizations.getOrganizationNetworks(orgId, total_pages='all')
        return networks
    except meraki.APIError as e:
        print(f'Meraki API error: {e}')
        print(f'status code = {e.status}')
        print(f'reason = {e.reason}')
        print(f'error = {e.message}')
    except Exception as e:
        print(f'some other error: {e}')

# Get Network Auth Users
def get_auth_users(networkId):
    try:
        users = m.networks.getNetworkMerakiAuthUsers(networkId)
        return users
    except meraki.APIError as e:
        print(f'Meraki API error: {e}')
        print(f'status code = {e.status}')
        print(f'reason = {e.reason}')
        print(f'error = {e.message}')
    except Exception as e:
        print(f'some other error: {e}')

# Get Network Auth Users
def delete_user(networkId, merakiAuthUserId):
    try:
        return m.networks.deleteNetworkMerakiAuthUser(
            networkId,
            merakiAuthUserId,
            delete=True
        )
    except meraki.APIError as e:
        print(f'Meraki API error: {e}')
        print(f'status code = {e.status}')
        print(f'reason = {e.reason}')
        print(f'error = {e.message}')
    except Exception as e:
        print(f'some other error: {e}')

#----------------------------------------------------------------------------#
# Available Functions 
#----------------------------------------------------------------------------#
def delete_network_guests(nework):
    users = get_auth_users(nework['id'])
    print(f"Network: {nework['name']} {nework['id']} - Total Users: {len(users)}")
    if len(users) == 0:
        return

    # Filter users by Account Type guest
    filtered_guests = filter_guests(users, 'guest')
    if len(filtered_guests) == 0:
        return

    # Filter users by domain
    filtered_emails = filter_emails(filtered_guests, excluded_domains)
    if len(filtered_emails) == 0:
        return

    # Filter users older than
    filtered_users = filter_dates(filtered_emails, older_than_days)
    if len(filtered_users) == 0:
        return

    print(f"Found {len(filtered_users)} to delete.")
    user_wants_to_continue()

    for user in filtered_users:
        # Skip the limit check if delete_x_users is None or non-positive
        try:
            print(delete_user(nework['id'], user['id']))
            print('Deleted:', user['name'])
        except:
            print('Failed to delete:', user['name'])
            continue

def delete_guests():
    selected_org_id = get_user_org_selection()

    # Provide Validation
    print(f"This will remove all guest users older than {older_than_days} days.")
    print(f"These email domains will be ignored:")
    for domain in excluded_domains:
        print(domain)

    networks = get_networks(selected_org_id)
    print(f"Found {len(networks)} networks.")

    user_wants_to_continue()

    for nework in networks:
        delete_network_guests(nework)


def unscoped_delete():
    from csv_filter import filter_guest_accounts
    from tkinter import Tk, filedialog

    # Hide the root Tkinter window
    Tk().withdraw()

    # Path to the CSV file
    filtered_guest_accounts = ""

    # Open a file dialog to select a CSV file
    file_path = filedialog.askopenfilename(
        filetypes=[("CSV files", "*.csv")],
        title="Choose a CSV file"
    )

    # Check if a file was selected
    if file_path:
        filtered_guest_accounts = filter_guest_accounts(file_path, older_than_days)
        print(filtered_guest_accounts)
    else:
        print("No file selected")

    print('Total Accounts: ',len(filtered_guest_accounts))

    selected_org_id = get_user_org_selection()

    network_name = 'Meraki Wireless Account Deletion'
    network = ''
    networks = get_networks(selected_org_id)
    for network in networks:
        if network["name"] == network_name:
            network = network
            break
    else:
        print(f'Create temporary network "{network_name}" to authorise users to allowing them to be deleted')
        user_wants_to_continue()

        network = m.organizations.createOrganizationNetwork(
            selected_org_id, network_name, ['wireless'], 
        )

        ssid = m.wireless.updateNetworkWirelessSsid(
            network["id"], 0, 
            name='Meraki Auth SSID', 
            enabled=False, 
            authMode='open',
            splashPage='Password-protected with Meraki RADIUS'
        )

        print('Temporary Network Setup')

    for account in filtered_guest_accounts:
        try:
            print(account['Email (Username)'])
            print(create_user(account['Email (Username)'], account['Description'], network["id"]))
        except:
            continue

    delete_network_guests(network)

#----------------------------------------------------------------------------#
# Main 
#----------------------------------------------------------------------------#

def main():
    selected_function = get_user_function()

    switcher = {
        1: delete_guests,
        2: unscoped_delete,
    }
    func = switcher.get(selected_function)
    func()
    

if __name__ == "__main__":
    main()



