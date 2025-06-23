import os
import re
from bs4 import BeautifulSoup

def process_html_file(file_path):
    """
    Applies a series of cleaning operations to a single HTML file.
    """
    print(f"Processing: {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # --- Task 1: Delete the UserWay widget script and noscript tag ---
        # This is a very specific block of code, so a direct string replacement is safe and efficient.
        userway_script_pattern = r'<script>\(function\(d\)\{var s = d\.createElement\("script"\);s\.setAttribute\("data-account", "tHALxNKsJo"\);s\.setAttribute\("src", "https://cdn\.userway\.org/widget\.js"\);\(d\.body \|\| d\.head\)\.appendChild\(s\);\}\)\(document\)</script><noscript>Please ensure Javascript is enabled for purposes of <a href="https://userway.org">website accessibility</a></noscript>'
        
        # Check if the script exists before replacing
        if re.search(userway_script_pattern, content):
            print("  - Found and removed UserWay accessibility widget.")
            content = re.sub(userway_script_pattern, '', content)
        
        # Parse the content with BeautifulSoup for more complex DOM manipulations
        soup = BeautifulSoup(content, 'lxml')

        # --- Task 2: Replace PressBooks platform link with local index.html ---
        # Find the <a> tag with a href pointing to the specified Open Textbooks domain.
        # Using a regex to catch potential variations like http/https or different subdomains.
        platform_link = soup.find('a', href=re.compile(r'https://opentextbooks\.col(vee)?\.org/?'))
        if platform_link:
            original_href = platform_link['href']
            platform_link['href'] = '../index.html'
            print(f'  - Replaced link "{original_href}" with "../index.html".')

        # --- Task 3: Delete the search form (label and button) ---
        # Find the search input field by its class
        search_input = soup.find('input', class_='search-field')
        if search_input:
            # The input is expected to be inside a <label> tag. We find and remove it.
            search_label = search_input.find_parent('label')
            
            # The button is expected to be the next sibling of the label
            search_button = search_label.find_next_sibling('button', class_='search-submit') if search_label else None

            if search_label and search_button:
                search_label.decompose()  # Removes the label and everything inside it
                search_button.decompose() # Removes the button
                print("  - Found and removed search form (label and button).")
            elif search_label:
                # If only the label is found, remove it.
                search_label.decompose()
                print("  - Found and removed search form label.")


        # --- Write the modified HTML back to the file ---
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        print(f"Finished: {file_path}\n")

    except Exception as e:
        print(f"Could not process file {file_path}. Error: {e}\n")


def traverse_and_clean_directory(directory):
    """
    Traverses a directory and applies the cleaning function to all .html files.
    """
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' not found.")
        return
        
    print(f"--- Starting cleanup in directory: {directory} ---\n")
    
    # os.walk will go through the target directory and all its subdirectories
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                process_html_file(file_path)
    
    print("--- Cleanup complete! ---")

# --- Main execution block ---
if __name__ == "__main__":
    # IMPORTANT: Set this to the path of your target folder.
    # Based on your image, the folder is named 'advancedcybersecuritytrainingteachers'.
    # You can use a relative path like this if the script is in the same parent directory,
    # or an absolute path (e.g., "C:/Users/YourUser/Documents/advancedcybersecuritytrainingteachers").
    target_folder = 'functionalfoods'
    
    # Before running, ensure you have the required libraries installed:
    # pip install beautifulsoup4
    # pip install lxml
    
    traverse_and_clean_directory(target_folder)
