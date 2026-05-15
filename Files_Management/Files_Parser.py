from Security.Advance_Logger import AdvancedLogger
from pathlib import Path
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
import pymupdf4llm
import openpyxl
import docx
import re

logger: AdvancedLogger = AdvancedLogger() 

class FileParser:
    def sanitize_text(user_input: str) -> str:
        """
        Removes potentially dangerous characters and trims whitespace.
        """
        if not isinstance(user_input, str):
            raise ValueError("Input must be a string")
        
        safe_text = re.sub(r"[^a-zA-Z0-9\s.,!?@#_-]", "", user_input)
        return safe_text.strip()

    @staticmethod
    def parse_pdf(path: str) -> str:
        try:
            markdown = pymupdf4llm.to_markdown(path)
            return markdown
        except Exception as e:
            logger.error("FileParser.parse_pdf", e)
            return ""
    
    @staticmethod
    def parse_docx(path: str) -> str:
        try:
            doc = docx.Document(path)
            full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            
            return full_text if full_text else ""
            
        except Exception as e:
            logger.error("FileParser.parse_docx", e)
            return "" 

    @staticmethod
    def extract_codebase(path: str) -> str:
        with open(path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")
    
    @staticmethod
    def extract_email(path: str) -> str:

        with open(path, "rb") as f:
            msg = BytesParser(
                policy=policy.default
            ).parse(f)

        body = None

        # Prefer plain text immediately
        for part in msg.walk():

            ctype = part.get_content_type()

            if ctype == "text/plain":

                try:
                    body = part.get_content()
                    break

                except Exception:
                    pass

        # Fallback to HTML
        if body is None:

            for part in msg.walk():

                if part.get_content_type() == "text/html":

                    try:

                        html = part.get_content()

                        soup = BeautifulSoup(
                            html,
                            "lxml"
                        )

                        for tag in soup([
                            "script",
                            "style",
                            "img",
                            "meta",
                            "head"
                        ]):
                            tag.decompose()

                        body = soup.get_text("\n")
                        break

                    except Exception:
                        pass

        if not body:
            body = ""

        lines = []

        append = lines.append

        for line in body.splitlines():

            line = line.strip()

            if not line:
                continue

            lower = line.lower()

            if (
                "unsubscribe" in lower
                or "tracking" in lower
                or "emailopen" in lower
            ):
                continue

            append(line)

        return "\n".join(lines)

    @staticmethod
    def parse_excel(path: str) -> str:
        try:
            rows = []
            append = rows.append
            
            if path.lower().endswith(".csv"):
                import csv

                with open(
                    path,
                    "r",
                    encoding="utf-8",
                    errors="ignore",
                    newline=""
                ) as f:

                    reader = csv.reader(f)

                    for row in reader:

                        values = [
                            str(cell).strip()
                            for cell in row
                            if cell not in (None, "")
                        ]

                        if values:
                            append(" | ".join(values))

                return "\n".join(rows).strip()
            wb = openpyxl.load_workbook(
                path,
                data_only=True,
                read_only=True
            )

            rows = []
            append = rows.append

            for sheet in wb.worksheets:

                append(f"\nSheet: {sheet.title}")

                for row in sheet.iter_rows(values_only=True):

                    values = [
                        str(cell).strip()
                        for cell in row
                        if cell is not None
                    ]

                    if values:
                        append(" | ".join(values))

            return "\n".join(rows).strip()

        except Exception as e:
            logger.error("FileParser.parse_excel", e)
            return ""
        
class ParseFile:

    PDF = ".pdf"
    DOCX = ".docx"
    EML = ".eml"

    XL = frozenset({
        ".xlsx", ".xls", ".csv"
    })

    CODE_EXTENSIONS = frozenset({
        ".py", ".js", ".ts", ".java",
        ".c", ".cpp", ".cs", ".go",
        ".rs", ".php", ".rb", ".swift",
        ".kt", ".html", ".css",
        ".json", ".xml", ".yaml",
        ".yml", ".txt"
    })

    @staticmethod
    def parse_any_file(path: str) -> str:

        try:

            suffix = Path(path).suffix.lower()

            # PDF
            if suffix == ParseFile.PDF:
                return FileParser.parse_pdf(path)

            # DOCX
            if suffix == ParseFile.DOCX:
                return FileParser.parse_docx(path)

            # EMAIL
            if suffix == ParseFile.EML:
                return FileParser.extract_email(path)

            # CODE / TEXT
            if suffix in ParseFile.CODE_EXTENSIONS:
                return FileParser.extract_codebase(path)
            
            if suffix in ParseFile.XL:
                return FileParser.parse_excel(path)

            # FALLBACK
            return FileParser.extract_codebase(path)

        except Exception as e:
            logger.error("ParseFile.parse_any_file", e)
            return ""
        
if __name__ == "__main__":
    lis = [r"F:\Smart AI workflow\Workflow\Log\Advance_Logger.py",r"F:\Testing\sample4.csv"]
    for i in lis:
        print(ParseFile.parse_any_file(i), "/n/nNew: ")