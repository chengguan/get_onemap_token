import requests
import getpass

email = input('email:')
password = getpass.getpass('Password:')

url = 'https://developers.onemap.sg/privateapi/auth/post/getToken'
myobj = {'email': email, 'password' : password}

resp = requests.post(url, json=myobj)

if (resp.status_code==200):
    try:
        token = resp.json()['access_token']
        expiry = resp.json()['expiry_timestamp']

        print(f"Access token: '{token}' will be expired at {expiry}.")
    except:
        print(resp.text)
else:
    print(resp.text)
