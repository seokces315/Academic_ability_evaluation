# Importing Modules
import fitz
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
                # Image Identifier
                xref = img[0]
                # Base Image
                base_image = doc.extract_image(xref)
                # Image Bytes
                image_bytes = base_image["image"]
                # Image Ext
                image_ext = base_image["ext"]
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


def main():

    # Local vars
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
    for i in range(len(raw_texts)):
        json_path = "../json/" + pdfs[i][:-4] + ".json"
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(raw_texts[i], json_file, ensure_ascii=False, indent=4)


# Run if script is called
if __name__ == "__main__":
    main()
