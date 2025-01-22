# Importing Modules
import fitz
import re
import json


# Method to extract raw data from PDF
def extract_pdf(paths):

    # Local vars
    texts = []
    images = []

    # Open pdf file with given paths
    for path in paths[:1]:

        # For each pdf file :
        text = []
        image = []
        doc = fitz.open(path)

        # Extract raw datum page by page
        for page in doc:
            # Image
            imgs = page.get_images(full=True)
            for _, img in enumerate(imgs):
                xref = img[0]  # Image Identifier
                base_image = doc.extract_image(xref)  # Base Image
                image_bytes = base_image["image"]  # Image Bytes
                image_ext = base_image["ext"]  # Image Ext

                # Generate tuple & Append
                img_pair = (image_bytes, image_ext)
                image.append(img_pair)

            # Text
            subtext = page.get_text("text")
            text.append(subtext)

        # Append raw images
        images.append(image)

        # Merge raw texts
        text = " ".join(text)
        texts.append(text)

    # Return : [], [] => Each pdf file's raw text/image
    return texts, images


# Method to split total corpus into paragraphs
def split_by_pgph(corpus):

    # Local vars
    paragraphs = []
    scopes = []

    # Find paragraphs' scope
    scopes = re.findall(r"\[\d+\s~\s\d+\]", corpus)

    # Split total corpus into paragraphs
    pgphs = re.split(r"\[\d+\s~\s\d+\]", corpus)
    for pgph in pgphs[1:]:
        pgph = re.split(r"답하시오.", pgph)
        paragraphs.append(pgph[1])

    return paragraphs, scopes


# Method to build json data objects
def generate_data_dict(date, scope, paragraph):

    # Local vars
    data_dict = dict()
    problems = []

    # ID
    rngs = []
    nums = re.split(r"\s~\s", scope[1:-1])
    rng = int(nums[1]) - int(nums[0]) + 1
    start = int(nums[0])
    for i in range(rng):
        rngs.append(start + i)
    for rng in rngs:
        if rn
    # for i in range(rng):
    #     if  < 10:
    #         rngs.append("0" + str(start + i))
    # data_dict["id"] = date[:-4] + "_" + nums[0] + "-" + nums[-1]

    # Cleansing
    clean_paragraph = re.sub(
        r"\n\d{4}학년도.*(\n.*){9}\n|\n.*\n국어영.*(\n.*){3}\n", "", paragraph
    )

    # Split into paragraph & question
    subpgphs = re.split(r"\n\d+\.\s*", clean_paragraph)

    # Paragraph : New line
    pgph = re.sub(r"\n", "", subpgphs[0])

    # Paragraph : Comma
    pgph = re.sub(r"\,", ", ", pgph)
    pgph = re.sub(r"\,\s+", ", ", pgph)

    # Paragraph : Punctuation
    pgph = re.sub(r"\.", ". ", pgph)
    pgph = re.sub(r"\.\s+", ". ", pgph)

    # Paragraph : Question mark
    pgph = re.sub(r"\?", "? ", pgph)
    pgph = re.sub(r"\?\s+", "? ", pgph)

    # Paragraph : Dash
    pgph = re.sub(r"\-", " -", pgph)
    pgph = re.sub(r"\s+\-", " -", pgph)

    # Paragraph : Double quotes
    pgph = re.sub(r"\s*\“", " “", pgph)
    pgph = re.sub(r"\s*\”", "” ", pgph)

    # Paragraph : Asterisk
    pgph = re.sub(r"\-\*", "- *", pgph)
    pgph = re.sub(r"\*\s+", "*", pgph)

    # Paragraph : Section
    pgph = re.sub(r"\(([가-사])\)", r"\n(\1) ", pgph)
    pgph = re.sub(r"\)\s+", ") ", pgph)

    # Paragraph : Syncopation
    pgph = re.sub(r"\(중략\)", "(중략) ", pgph)

    if pgph[0] == "\n":
        pgph = pgph[1:]
    data_dict["paragraph"] = pgph[:-1]

    # Type
    data_dict["type"] = 0

    # Subject
    data_dict["paragraph_subject"] = "TODO"

    # Problems
    print(subpgphs[1:])
    print(rngs)

    # for i in range(1):
    # # for i in range(subpgphs[1:]):
    #     problem = dict()
    #     problem["question_id"] = date[:-4]

    return data_dict


def main():

    # Local vars
    data_dicts = []
    p_id = "Kor_3rd_202"

    # Generate pdf list
    pdfs = []
    for i in range(3):
        year = str(i + 2) + "_"
        pdfs.append(p_id + year)

    months = ["03", "04", "07", "10"]
    for i in range(3):
        for month in months:
            month += ".pdf"
            pdfs.append(pdfs[i] + month)

    # Post-process
    pdfs = pdfs[3:]
    pdfs[-3] = "Kor_3rd_2024_05.pdf"
    # pdfs[-1] = "Kor_3rd_2022_03_해설.pdf"

    # Define documents' path
    paths = ["../data/Kor_3rd/" + pdf for pdf in pdfs]

    # Extract documents' raw datum
    raw_texts, raw_images = extract_pdf(paths)

    # Save images in certain directory
    for i in range(len(raw_images)):
        image_og_path = "../image/" + pdfs[i][:-4] + "_"
        for idx, img_pair in enumerate(raw_images[i]):
            image_path = image_og_path + str(idx + 1) + "." + img_pair[1]
            with open(image_path, "wb") as image_file:
                image_file.write(img_pair[0])

    # Prototype : Corpus
    paragraphs = []
    for i in range(len(raw_texts)):
        paragraphs, scopes = split_by_pgph(raw_texts[i])
        for j in range(1):
            # for j in range(len(scopes)):
            data_dict = generate_data_dict(pdfs[i], scopes[j], paragraphs[j])
            data_dicts.append(data_dict)

        json_path = "../json/" + pdfs[i][:-4] + ".json"
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(data_dicts, json_file, ensure_ascii=False, indent=4)
        with open("raw text", "w", encoding="utf-8") as json_file:
            json.dump(raw_texts[0], json_file, ensure_ascii=False, indent=4)


# Run if script is called
if __name__ == "__main__":
    main()
