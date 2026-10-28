
from pathlib import Path
import pandas as pd
from langchain_core.documents import Document


def load_excel(file_path: str):
    """Load Excel sheets as row-level Documents."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    all_documents = []

    sheets = pd.read_excel(
        path,
        sheet_name=None,
    )

    for sheet_name, dataframe in sheets.items():

        dataframe = dataframe.fillna("")

        for row_number, row in dataframe.iterrows():

            row_text = "\n".join(
                f"{column}: {value}"
                for column, value in row.items()
                if str(value).strip()
            )

            if not row_text.strip():
                continue

            document = Document(
                page_content=row_text,
                metadata={
                    "source": path.name,
                    "file_type": "excel",
                    "sheet_name": sheet_name,
                    "row_number": int(row_number) + 2,
                },
            )

            all_documents.append(document)

    return all_documents
