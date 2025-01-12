import os
import requests
from bs4 import BeautifulSoup
import zipfile
import tempfile

# Set API endpoint URL and parameters
OLLAMA_API = "http://localhost:11434/api/chat"
HEADERS = {"Content-Type": "application/json"}
MODEL = "llama3.2"

# Constant URL for the package
PACKAGE_URL = "https://archiva.interlocsolutions.com/archiva/repository/internal/com/github/bumptech/glide/disklrucache/4.14.2/disklrucache-4.14.2-sources.jar"

# Function to extract files from the archive
def extract_archive(archive_path, temp_folder):
    package_name = os.path.basename(archive_path)
    
    # Create a new folder with the same name as the archive
    new_folder_path = os.path.join(temp_folder, package_name)
    
    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)

    # Get the list of files in the archive
    file_list = []
    for root, dirs, files in zipfile.ZipInfoNamesIter(archive_path):
        file_list.append(os.path.basename(root))

    # Extract each file from the archive
    for file_name in file_list:
        if file_name.endswith('.jar'):
            file_path = os.path.join(new_folder_path, file_name)
            with open(file_path, 'wb') as f:
                f.write(zipfile.ZipFile(archive_path, 'r').read(file_name))
        else:
            file_path = os.path.join(new_folder_path, file_name)
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, 'wb') as f:
                f.write(zipfile.ZipFile(archive_path, 'r').read(file_name))

# Function to get API response for copyright detection
def get_copyrights(api_url, file_path):
    data = {
        "model": MODEL,
        "prompt": f"Detect the copyrights in this code:\n\n" + open(file_path, 'r').read()
    }
    response = requests.post(api_url, headers=HEADERS, json=data)
    return response.json()

# Function to get package name from URL
def get_package_name(url):
    api_url = url.replace('https://', '')
    data = {
        "url": api_url
    }
    
    # Send request to OLLAMA_API to identify the file name
    response = requests.get(api_url + '/api/v1/package')
    if response.status_code == 200:
        package_name = response.json()['name']
        return package_name
    else:
        print(f"Failed to retrieve package name: {response.status_code}")
        return None

# Main function to process the archive
def main():
    # Get the current working directory
    cwd = os.getcwd()

    print(f"Creating temporary folder in: {cwd}")

    temp_folder = tempfile.mkdtemp(dir=cwd)

    package_name = get_package_name(PACKAGE_URL)
    
    if package_name:
        with open(os.path.join(temp_folder, package_name), 'wb') as f:
            response = requests.get(PACKAGE_URL)
            f.write(response.content)
        
        extract_archive(os.path.join(temp_folder, package_name), temp_folder)

        copyrights = set()
        for root, dirs, files in os.walk(temp_folder):
            for dir in dirs:
                file_path = os.path.join(root, dir)
                if not os.path.basename(file_path).startswith('.'):
                    api_url = OLLAMA_API + '/api/v1/package/' + package_name
                    response = requests.get(api_url)
                    data = response.json()
                    if 'licenses' in data:
                        copyrights.update(data['licenses'])

        print("Unique copyrights:")
        for copyright in copyrights:
            print(copyright)

    # Delete the temporary folder
    import shutil
    shutil.rmtree(temp_folder)

if __name__ == "__main__":
    main()