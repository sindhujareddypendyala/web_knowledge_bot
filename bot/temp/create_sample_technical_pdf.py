from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


output_dir = Path("output/pdf")
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "sample_technical_api_guide.pdf"

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1F4E79"),
        spaceBefore=12,
        spaceAfter=6,
    )
)
styles.add(
    ParagraphStyle(
        name="BodyTextSpaced",
        parent=styles["BodyText"],
        leading=15,
        spaceAfter=8,
    )
)

doc = SimpleDocTemplate(
    str(output_path),
    pagesize=letter,
    rightMargin=0.7 * inch,
    leftMargin=0.7 * inch,
    topMargin=0.7 * inch,
    bottomMargin=0.7 * inch,
)

story = []
story.append(Paragraph("SecureDocs API Technical Guide", styles["Title"]))
story.append(
    Paragraph(
        "Version 1.0 - Backend integration reference for authentication, endpoints, rate limits, and error handling.",
        styles["BodyTextSpaced"],
    )
)

story.append(Paragraph("1. Authentication", styles["SectionTitle"]))
story.append(
    Paragraph(
        "SecureDocs API uses bearer token authentication. Every protected request must include an Authorization header in the format: Authorization: Bearer YOUR_ACCESS_TOKEN. Tokens expire after 60 minutes and should be refreshed using the /auth/refresh endpoint.",
        styles["BodyTextSpaced"],
    )
)
story.append(
    Paragraph(
        "If the token is missing, expired, or invalid, the API returns HTTP 401 with the error code AUTH_INVALID_TOKEN.",
        styles["BodyTextSpaced"],
    )
)

story.append(Paragraph("2. Core Endpoints", styles["SectionTitle"]))
endpoint_data = [
    ["Method", "Endpoint", "Purpose"],
    ["POST", "/documents", "Upload a PDF document for processing."],
    ["GET", "/documents/{document_id}", "Fetch document metadata and processing status."],
    ["POST", "/query", "Ask a question against indexed technical documents."],
    ["DELETE", "/documents/{document_id}", "Delete a document and all vector chunks."],
]
table = Table(endpoint_data, colWidths=[0.9 * inch, 2.1 * inch, 3.0 * inch])
table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17365D")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]
    )
)
story.append(table)
story.append(Spacer(1, 10))

story.append(Paragraph("3. Rate Limits", styles["SectionTitle"]))
story.append(
    Paragraph(
        "The API allows 120 requests per minute per API key. When the limit is exceeded, the API returns HTTP 429 with the error code RATE_LIMIT_EXCEEDED. Clients should retry after the number of seconds provided in the Retry-After response header.",
        styles["BodyTextSpaced"],
    )
)

story.append(Paragraph("4. Error Handling", styles["SectionTitle"]))
story.append(
    Paragraph(
        "All error responses use JSON with fields: error_code, message, and request_id. The request_id should be logged by client applications and included when reporting issues to support.",
        styles["BodyTextSpaced"],
    )
)
story.append(
    Paragraph(
        "Common errors include VALIDATION_ERROR for malformed JSON, DOCUMENT_NOT_FOUND for unknown document IDs, and UNSUPPORTED_FILE_TYPE when a non-PDF file is uploaded.",
        styles["BodyTextSpaced"],
    )
)

story.append(Paragraph("5. Security Recommendations", styles["SectionTitle"]))
story.append(
    Paragraph(
        "Store API tokens in environment variables or a secure secret manager. Never commit tokens to source control. Use HTTPS for all production traffic and rotate access tokens at least every 90 days.",
        styles["BodyTextSpaced"],
    )
)

doc.build(story)
print(output_path.resolve())
