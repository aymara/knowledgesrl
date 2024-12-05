import sys
import os
import re

def remove_comments(input_file, output_file):
    """
    Processes a text file to :
    1. Delete lines beginning with '#'.
    2. Replace double (or multiple) empty lines with a single empty line.

    Args:
    input_file (str): Input file path.
    output_file (str): Output file path.
    """
    try:
        with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
            content = infile.read()

            # Delete lines beginning with '#'.
            lines = content.splitlines()
            filtered_lines = [line for line in lines if not line.strip().startswith("#")]

            # Join filtered lines with line breaks
            filtered_text = "\n".join(filtered_lines)

            # Replace double (or multiple) empty lines with a single line
            cleaned_text = re.sub(r"\n\s*\n", "\n\n", filtered_text)

            # Write the cleaned text to the output file
            outfile.write(cleaned_text)
        print(f"File processed and saved in : {output_file}")
    except Exception as e:
        print(f"Processing errors : {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage : python process_text.py <input_file> <output_file>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]

        if not os.path.exists(input_file):
            print(f"Error: file '{input_file}' does not exist.")
        else:
            remove_comments(input_file, output_file)
