import os

contracts_folder = "full_contract_txt"

if not os.path.isdir(contracts_folder):
    print("Contracts folder not found.")
else:
    for file in os.listdir(contracts_folder):
        if file.endswith(".txt"):
            file_path = os.path.join(contracts_folder, file)
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            print(f"\n=== {file} ===")
            print(text[:1000])
            print("\n=== End of Preview ===")
