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
    for path in paths:

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
    q_nums = []
    t_b = re.split(r"\s~\s", scope[1:-1])
    rng = int(t_b[-1]) - int(t_b[0]) + 1
    for i in range(rng):
        num = int(t_b[0]) + i
        q_num = "0" + str(num) if num < 10 else str(num)
        q_nums.append(q_num)
    data_dict["id"] = date[:-4] + "_" + q_nums[0] + "-" + q_nums[-1]

    # Cleansing
    clean_paragraph = re.sub(
        r"\n.*학력평가.*\n국어영역(\n.*){8}\n|"
        r"\n.*학력평가.*\n.*\(화법과작문\)(\n.*){7}\n",
        "",
        paragraph,
    )

    clean_paragraph = re.sub(
        r"\n<그림>.*\n.*고3\n국어영역(\n.*){3}|"
        r"\n\[A\](\n.*)*\n.*고3\n국어영역.*(\n.*){3}",
        "",
        clean_paragraph,
    )

    clean_paragraph = re.sub(
        r"\n.*고3\n국어영역(\n.*){3}|"
        r"\n.*\n국어영역.*\n고3(\n.*){2}|"
        r"\n\[A\]\n.*고3\n국어영역.*(\n.*){3}|"
        r"(\n.*){3}\n.*이어서.*선택과목.*(\n.*)*\n",
        "",
        clean_paragraph,
    )

    # Split into paragraph & question
    subpgphs = re.split(r"\.\s*\n\d+\.\s*|\-\s*\n\d+\.\s*", clean_paragraph)

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
    data_dict["paragraph"] = pgph + "."
    if data_dict["paragraph"][-3] == "｣":
        data_dict["paragraph"] = data_dict["paragraph"][:-1] + "-"

    # Type
    data_dict["type"] = 0

    # Subject
    data_dict["paragraph_subject"] = "TODO"

    # Problems
    for i in range(len(subpgphs[1:])):
        # For each problem :
        problem = dict()

        # Question ID
        problem["question_id"] = date[:-4] + "_" + q_nums[i]

        # Problems : New line
        question = re.sub(r"\n", "", subpgphs[i + 1])

        # Question
        question = re.split(r"\?", question)
        query = re.sub(r"～", "~", question[0])
        query = re.sub(r"~ ", "~", query)
        problem["question"] = query + "?"
        try:
            question = re.split(r"<\s보\s기\s>", question[1])
        except:
            pass

        # Example & Choices
        choices = []
        choice = re.split(r"[①②③④⑤]", question[-1])
        if len(choice[0]) > 1:
            # Example : Comma
            example = re.sub(r"\,", ", ", choice[0])
            example = re.sub(r"\,\s+", ", ", example)

            # Example : Punctuation
            example = re.sub(r"\.", ". ", example)
            example = re.sub(r"\.\s+", ". ", example)
            example = re.sub(r"\. \)", ".) ", example)

            # Example : Question mark
            example = re.sub(r"\?\s+", "? ", example)
            example = re.sub(r"\?", "? ", example)

            # Example : Dash
            example = re.sub(r"\-", " -", example)
            example = re.sub(r"\s+\-", " -", example)

            # Example : Double quotes
            example = re.sub(r"\s*\“", " “", example)
            example = re.sub(r"\s*\”", "” ", example)

            # Example : Asterisk
            example = re.sub(r"\-\*", "- *", example)
            example = re.sub(r"\*\s+", "*", example)

            # Example : Series of dot
            example = re.sub(r"\·\s([ⓐⓑⓒⓓ㉠㉡㉢㉣㉤])", r"· \1\n", example)

            example = example.rstrip()

            if "<보기>" in problem["question"]:
                problem["question_plus"] = "< 보 기 >\n" + example
            else:
                if "[3점]" in example:
                    problem["question_plus"] = example[5:]
                else:
                    problem["question_plus"] = example

        choice = choice[1:]
        for i in range(len(choice)):
            choice[i] = choice[i].strip()
            try:
                if choice[i][-1] != ".":
                    choices.append(choice[i] + ".")
                else:
                    choices.append(choice[i])
            except:
                choices.append(choice[i])
        problem["choices"] = choices

        # Answer
        problem["answer"] = 0

        # Score
        if "[3점]" in question[0]:
            problem["score"] = 3
        else:
            problem["score"] = 2

        # Question type
        problem["question_type"] = "TODO"

        problems.append(problem)

    data_dict["problems"] = problems

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
    idx_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    for idx in idx_list:
        paragraphs, scopes = split_by_pgph(raw_texts[idx])

        # with open("raw text", "w", encoding="utf-8") as json_file:
        #     json.dump(raw_texts[1], json_file, ensure_ascii=False, indent=4)

        for j in range(len(scopes)):
            data_dict = generate_data_dict(pdfs[idx], scopes[j], paragraphs[j])
            data_dicts.append(data_dict)

        json_path = "../json/" + pdfs[idx][:-4] + ".json"
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(data_dicts, json_file, ensure_ascii=False, indent=4)


# Run if script is called
if __name__ == "__main__":
    main()
