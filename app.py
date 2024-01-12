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
    '@cisco.com',
    '@meraki.net'
]

older_than_days = 30

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

def create_test_user(email, networkId):
    return m.networks.createNetworkMerakiAuthUser(
        networkId,
        email=email,
        name=f"Guest Test",
        accountType="Guest",
        password=(''.join(secrets.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_-+=<>?") for _ in range(12))),
        authorizations = [
            {
                "ssidNumber": 0,
                "expiresAt": "2024-03-13T00:00:00.090210Z"
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
# Main 
#----------------------------------------------------------------------------#

def main():
    orgs = get_organisations()
    print(orgs)
    if not orgs:
        print("No organizations found.")
        return

    sorted_orgs = sorted(orgs, key=lambda x: x['name'])
    display_list(sorted_orgs, 'Organizations')
    
    selected_org_id, org_name = get_user_selection(sorted_orgs)

    print(f"\nSelected Organization: {org_name} - {selected_org_id}")

    # Provide Validation
    print(f"This will remove all guest users older than {older_than_days} days.")
    print(f"These email domains will be ignored:")
    for domain in excluded_domains:
        print(domain)

    networks = get_networks(selected_org_id)
    print(f"Found {len(networks)} networks.")

    user_wants_to_continue()

    for nework in networks:
        users = get_auth_users(nework['id'])
        print(f"Network: {nework['name']} {nework['id']} - Total Users: {len(users)}")

        if len(users) == 0:
            continue

        # Filter users by Account Type guest
        filtered_guests = filter_guests(users, 'guest')
        if len(filtered_guests) == 0:
            continue

        # Filter users by domain
        filtered_emails = filter_emails(filtered_guests, excluded_domains)
        if len(filtered_emails) == 0:
            continue

        # Filter users older than
        filtered_users = filter_dates(filtered_emails, older_than_days)
        if len(filtered_users) == 0:
            continue

        print(f"Found {len(filtered_users)} to delete.")
        user_wants_to_continue()

        for user in filtered_users:
            try:
                delete_user(nework['id'], user['id'])
                print('Deleted:', user['name'])
            except:
                print('Failed to delete:', user['name'])
                continue
            
    
if __name__ == "__main__":
    main()
