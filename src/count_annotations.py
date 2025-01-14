import os

def count_annotated_sentences_in_file(conll_file):
    """Counts sentences with annotations in a single CoNLL file."""
    annotated_sentence_count = 0  # To count sentences with annotations
    current_sentence_has_annotation = False

    with open(conll_file, "r") as file:
        for line in file:
            line = line.strip()
            
            
            if line == "":  # End of a sentence
                if current_sentence_has_annotation:
                    annotated_sentence_count += 1
                current_sentence_has_annotation = False  # Reset for the next sentence
            else:
                columns = line.split("\t")
                if len(columns) >= 10 and ((columns[9]!="_") or (columns[10]!="_")):
                    current_sentence_has_annotation = True

    # In case the last sentence does not end with an empty line
    if current_sentence_has_annotation:
        annotated_sentence_count += 1

    return annotated_sentence_count

def count_annotated_sentences_in_folder(folder_path):
    """Counts annotated sentences in all CoNLL files within a folder."""
    total_annotated_sentences = 0
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".conll"):  # Process only .conll files
            file_path = os.path.join(folder_path, file_name)
            print(f"Processing file: {file_name}")
            count = count_annotated_sentences_in_file(file_path)
            total_annotated_sentences += count
            print(f"  Annotated sentences in {file_name}: {count}")
    return total_annotated_sentences

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python script.py <conll_folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    
    if not os.path.isdir(folder_path):
        print(f"The provided folder path does not exist: {folder_path}")
        sys.exit(1)

    total_count = count_annotated_sentences_in_folder(folder_path)
    print(f"\nTotal annotated sentences in the folder: {total_count}")

