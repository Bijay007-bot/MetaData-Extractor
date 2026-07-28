# MetaData-Extractor
# Digital Forensics Metadata Extractor

A desktop application for extracting and reviewing metadata from image and PDF
files. The project was developed in Python for the ST4017CMD Introduction to
Programming coursework.

## Student details

- **Student:** Bijay Raj Chapai
- **Student ID:** 260155
- **Module:** ST4017CMD Introduction to Programming
- **Institution:** Softwarica College of IT & E-Commerce

## Project overview

Files often contain hidden information such as creation dates, device details,
software names, author information, and GPS coordinates. This application
provides a simple graphical interface for viewing that metadata. It separates
ordinary values from fields that may require additional attention during a
digital-forensics review.

The tool is intended for educational use. Only inspect files that you own or
have permission to analyse.

## Main features

- Extracts metadata from JPG, JPEG, PNG, TIFF, BMP, GIF, WebP, and PDF files.
- Displays basic file details, image dimensions, EXIF tags, and PDF properties.
- Converts EXIF GPS coordinates from degrees, minutes, and seconds to decimal
  degrees.
- Creates a Google Maps link when usable GPS data is present.
- Labels fields as normal, noteworthy, or sensitive.
- Allows a metadata value to be copied by double-clicking its row.
- Exports the displayed results as a text report.
- Handles missing libraries, invalid files, and unsupported formats.

## Technologies used

- Python 3.9 or later
- Tkinter for the graphical interface
- Pillow for image and EXIF processing
- PyPDF2 for PDF metadata processing
- `unittest` for automated tests

## Repository structure

```text
.
├── index.py
├── README.md
├── requirements.txt
├── .gitignore
└── tests
    └── test_metadata_extractor.py
```

## Installation

### 1. Clone the GitHub Classroom repository

```bash
git clone YOUR_GITHUB_CLASSROOM_REPOSITORY_URL
cd YOUR_REPOSITORY_FOLDER
```

### 2. Create a virtual environment

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install the dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Tkinter is included with most standard Python installers. On Ubuntu or Debian,
install it separately if Python reports that the module is missing:

```bash
sudo apt install python3-tk
```

## Running the application

```bash
python index.py
```

If `python` is not recognised on macOS or Linux, use:

```bash
python3 index.py
```

## How to use

1. Select **Browse File**.
2. Choose a supported image or PDF that you are authorised to inspect.
3. Review the metadata fields and their colour-coded categories.
4. Double-click a row to copy its value.
5. Select **Export .txt** to save the displayed metadata.
6. Select **Clear** before analysing another file if required.

## Running the tests

Run all automated tests from the repository root:

```bash
python -m unittest discover -s tests -v
```

The test suite checks:

- metadata classification;
- GPS coordinate conversion;
- plain-image extraction;
- EXIF extraction and field categories;
- PDF metadata extraction;
- missing-file error handling;
- unsupported file rejection; and
- image dispatch through the application logic.

## Ethical and technical limitations

- Metadata can be removed, changed, or forged, so it should not be treated as
  proof on its own.
- Some images do not contain EXIF information.
- Encrypted, damaged, or unusual PDF files may not expose readable metadata.
- The current version analyses one local file at a time.
- The application does not modify the selected source file.

## Version-control workflow

Development should be recorded through regular, meaningful commits. Example
branches are:

- `feature/image-exif`
- `feature/pdf-metadata`
- `feature/gui`
- `test/metadata`

Example commit messages:

```text
Initialise Python metadata extractor project
Add image and EXIF metadata extraction
Add PDF metadata extraction
Build Tkinter interface and risk labels
Add text export and clipboard support
Add automated metadata tests
Complete README and release cleanup
```

## Author

Bijay Raj Chapai — Student ID 260155
