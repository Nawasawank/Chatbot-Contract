import requests

def upload_to_fileio(file_path):
    with open(file_path, 'rb') as file:
        response = requests.post('https://file.io/', files={'file': file})
        response_json = response.json()
        file_link = response_json.get('link')
    return file_link

