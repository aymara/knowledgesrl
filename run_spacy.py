import spacy
import argparse

def analyze_text(text):
    # Load the French language model
    nlp = spacy.load("fr_core_news_sm")

    # Process the text
    doc = nlp(text)

    # Initialize the CoNLL-U format string
    conllu_format = "# sent_id = 1\n# text = {}\n".format(text)

    # Iterate over tokens in the processed document
    for i, token in enumerate(doc):
        # Format each token in CoNLL-U format and append to the result string
        conllu_format += "{}\t{}\t{}\t{}\t{}\t_\t{}\t{}\t_\t_\n".format(
            i + 1,  # ID
            token.text,  # Form
            token.lemma_,  # Lemma
            token.pos_,  # POS
            token.tag_,  # Morphological features
            token.dep_,  # Dependency label
            token.head.i + 1 if token.head != token else "0"  # Head
        )

    return conllu_format

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Analyze a French text with SpaCy and write the result in CoNLL-U format")
    parser.add_argument("filename", type=str, help="Path to the file containing the French text")

    # Parse the command line arguments
    args = parser.parse_args()

    # Read text from file
    with open(args.filename, "r", encoding="utf-8") as file:
        text = file.read()

    # Analyze the text
    result = analyze_text(text)

    # Print the result
    print(result)

if __name__ == "__main__":
    main()
