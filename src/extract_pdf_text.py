import pdfplumber # type: ignore
import sys
import os
import re

def clean_text(text):
    """
    Cleans up text by removing :
    - Special characters such as , , and similar symbols
    - Lines of type “..... 1” or containing repeating dots
    - Periods and spaces at the beginning of lines
    - Lines composed entirely of irrelevant characters
    - Section numbers (e.g., “5.3”)
    - Unnecessary spaces and lines
    - Unnecessary line breaks if the next line begins with a lowercase letter
    """
    # Removes Special characters such as , , and similar symbols
    text = re.sub(r"[•]", "", text)
    
    # Removes Lines of type “..... 1” or containing repeating dots
    text = re.sub(r"\s*\.+\s*\d*\s*$", "", text, flags=re.MULTILINE)

    # Removes Section numbers (e.g., “5.3”)
    text = re.sub(r"^\s*\d+(\.\d+)*\s*", "", text, flags=re.MULTILINE)

    # Removes Lines composed entirely of irrelevant characters
    text = re.sub(r"^\W+$", "", text, flags=re.MULTILINE)

    # Removes Unnecessary spaces at the beginning or ending of a line
    text = re.sub(r"^\s+|\s+$", "", text, flags=re.MULTILINE)

    # Removes Empty lines
    text = re.sub(r"\n\s*\n", "\n", text)
    
    # Removes Periods and spaces at the beginning of lines
    text = re.sub(r"^\.\s*", "", text, flags=re.MULTILINE)
    
    # Removes Unnecessary line breaks if the next line begins with a lowercase letter
    text = re.sub(r"\n([a-z])", r" \1", text)

    # Removes phrases of type "Page X of Y" for any numbers X and Y
    text = re.sub(r"Page\s+\d+\s+sur\s+\d+", "", text, flags=re.IGNORECASE)

    return text

def extract_text_from_pdf(input_pdf, output_txt=None):
    try:
        if output_txt is None:
            output_txt = os.path.splitext(input_pdf)[0] + ".txt"

        with pdfplumber.open(input_pdf) as pdf:
            with open(output_txt, "w", encoding="utf-8") as f:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text:
                        # Cleans the text before writing in the file
                        cleaned_text = clean_text(text)
                        f.write(cleaned_text + "\n")
                    else:
                        f.write(f"--- Page {page_num} is empty or contains non-extractable content ---\n")
        
        print(f"Text succesfully extracted in the following folder : {output_txt}")
    except FileNotFoundError:
        print(f"Error : The file '{input_pdf}' was not found.")
    except Exception as e:
        print(f"An error occured : {e}")

def process_folder(input_folder, output_folder):
    """
    Deals with the pdf files in a folder and saves the created txt files in another folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".pdf"):
            input_pdf = os.path.join(input_folder, filename)
            output_txt = os.path.join(output_folder, os.path.splitext(filename)[0] + ".txt")
            print(f"Current file : {input_pdf}")
            extract_text_from_pdf(input_pdf, output_txt)

if __name__ == "__main__":
    # Vérifier les arguments passés
    if len(sys.argv) < 2:
        print("Using : python script.py <dossier_pdf>")
    else:
        input_folder = sys.argv[1]
        parent_folder = os.path.dirname(input_folder)
        output_folder = os.path.join(parent_folder, "DataInTxtFormat")

        print(f"Processing the PDF files in : {input_folder}")
        print(f"The TXT files will be saved here : {output_folder}")

        process_folder(input_folder, output_folder)

        print(f"All the PDF files have been converted to TXT. You may find them at : {output_folder}")

