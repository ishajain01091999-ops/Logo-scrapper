import os

# Extension ID
extension_id = "gabfmnliflodkdafenbcpjdlppllnemd"

# Chrome user data root
chrome_user_data = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")

found = False

# Loop through all profile folders
for profile in os.listdir(chrome_user_data):
    profile_path = os.path.join(chrome_user_data, profile, "Extensions", extension_id)
    if os.path.exists(profile_path):
        print(f"Extension found in profile: {profile}")
        print("Path:", profile_path)
        print("Subfolders (versions):", os.listdir(profile_path))
        found = True

if not found:
    print("Extension not found in any profile. Maybe it's installed in another Chrome user or not installed at all.")
