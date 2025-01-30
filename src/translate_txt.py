from googletrans import Translator # type: ignore
import sys
import os
import asyncio

async def translate_file(input_txt, output_txt=None, src_lang="fr", dest_lang="en"):
    """
    Translates a text file line by line from a source language to a target language.

    - param input_txt: Path of input text file
    - param output_txt: Path of output text file (optional)
    - param src_lang: Source language code (e.g. “fr” for French)
    - param dest_lang: Target language code (e.g. “en” for English)
    """
    try:
        if output_txt is None:
            output_txt = os.path.splitext(input_txt)[0] + "_translated.txt"

        translator = Translator()

        # Reads and translates the file
        with (open(input_txt, "r", encoding="utf-8") as infile,
              open(output_txt, "w", encoding="utf-8") as outfile):
            for line_num, line in enumerate(infile, start=1):
                # Removes the unnecessary spaces
                line = line.strip()

                if line:  # Translates only if the line isn't empty
                    try:
                        result = await translator.translate(line,
                                                            src=src_lang,
                                                            dest=dest_lang)
                        translated = result.text
                        outfile.write(translated + "\n")
                    except Exception as e:
                        print(f"Error translating the line {line_num}: {e}")
                        outfile.write(
                            f"--- Line not translated (Error) : {line}\n")
                else:
                    # If the line is empty, add an empty line to the output
                    # file
                    outfile.write("\n")

        print(f"File successfully translated : {output_txt}")
    except FileNotFoundError:
        print(f"Error: The file '{input_txt}' was not found.")
    except Exception as e:
        print(f"An error has occurred : {e}")

async def process_folder(input_folder, output_folder):
    """
    Translates all files in one folder and saves them as TXT files in another folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".txt"):
            input_pdf = os.path.join(input_folder, filename)
            output_txt = os.path.join(output_folder, os.path.splitext(filename)[0] + "_translated.txt")
            print(f"Processing of the file : {input_pdf}")
            await translate_file(input_pdf, output_txt)


async def main():
    # Vérifier les arguments passés
    if len(sys.argv) < 2:
        print("Using : python translate_txt.py <dossier_pdf>")
    else:
        input_folder = sys.argv[1]
        parent_folder = os.path.dirname(input_folder)
        output_folder = os.path.join(parent_folder, "DataEngInTxtFormat")

        print(f"Original folder containing the TXT files : {input_folder}")
        print(f"Translated files in the following folder : {output_folder}")

        await process_folder(input_folder, output_folder)

        print(f"All files have been processed successfully. Translated files can be found in : {output_folder}")

if __name__ == "__main__":
    asyncio.run(main())

