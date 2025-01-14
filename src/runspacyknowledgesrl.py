import os
import sys
import subprocess

def process_files(input_folder, model_used):
    # Define output folders
    engtxt_input_folder = os.path.join(input_folder, 'DataEngInTxtFormat/')
    spacy_output_folder = os.path.join(input_folder, "RunSpacyDataEngCarnopital/")
    clean_output_folder = os.path.join(input_folder, "RunSpacyCleanDataEngCarnopital/")
    final_output_folder = os.path.join(input_folder, "OutDataCarnopitalKSRL/")

    # Create output directories if they don't exist
    os.makedirs(spacy_output_folder, exist_ok=True)
    os.makedirs(clean_output_folder, exist_ok=True)
    os.makedirs(final_output_folder, exist_ok=True)

    # Process each file in the input directory
    for file_name in os.listdir(engtxt_input_folder):
        if file_name.endswith(".txt"):  # Check if the file is a .txt file
            input_file = os.path.join(engtxt_input_folder, file_name)
            
            # Construct output file names
            base_name = os.path.splitext(file_name)[0]
            spacy_output_file = os.path.join(spacy_output_folder, f"{base_name}.conll")
            clean_output_file = os.path.join(clean_output_folder, f"{base_name}.conll")
            final_output_file = os.path.join(final_output_folder, f"{base_name}.conll")

            try:
                # Step 1: Run run_spacy.py
                spacy_command = [
                    "python", "run_spacy.py",
                    "--input_file", input_file,
                    "--model",  model_used,
                ]
                with open(spacy_output_file, "w") as spacy_out:
                    #print(f"Running: {' '.join(spacy_command)}")
                    subprocess.run(spacy_command, stdout=spacy_out, check=True)

                # Step 2: Run remove_comments.py
                remove_comments_command = [
                    "python", "src/remove_comments.py",
                    spacy_output_file, clean_output_file
                ]
                #print(f"Running: {' '.join(remove_comments_command)}")
                subprocess.run(remove_comments_command, check=True)

                # Step 3: Run knowledgesrl.py
                srl_command = [
                    "python", "src/knowledgesrl.py",
                    "--language=eng",
                    "--frame-lexicon=FrameNet",
                    f"--conll-input={clean_output_file}",
                    f"--conll-output={final_output_file}"
                ]
                #print(f"Running: {' '.join(srl_command)}")
                subprocess.run(srl_command, check=True)

                print(f"Processing completed for {file_name}")
            except subprocess.CalledProcessError as e:
                print(f"Error processing {file_name}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_directory>")
        sys.exit(1)

    input_directory = sys.argv[1]
    model_used = sys.argv[2]
    
    if not os.path.isdir(input_directory):
        print(f"The provided directory does not exist: {input_directory}")
        sys.exit(1)

    process_files(input_directory, model_used)

