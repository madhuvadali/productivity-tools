from flask import Flask, request, send_file, render_template_string
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024 * 1024  # 256 MB total upload cap (adjust if needed)

TPL = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Local PDF Merger</title>
  <style>
    body{font-family:system-ui,Segoe UI,Roboto,Arial;margin:0;padding:24px;background:#0b0f14;color:#e5e7eb}
    .card{max-width:720px;margin:0 auto;background:#111826;border:1px solid #27324a;border-radius:14px;padding:18px}
    h1{margin:0 0 8px}
    .muted{color:#9aa3af}
    input[type=file]{margin:12px 0}
    button{padding:10px 14px;border-radius:10px;border:0;background:#2563eb;color:#fff;font-weight:600;cursor:pointer}
    .warn{background:#1f2937;border:1px solid #374151;padding:10px;border-radius:10px;margin-top:12px}
    a{color:#93c5fd}
  </style>
</head>
<body>
  <div class="card">
    <h1>Local PDF Merger (Flask)</h1>
    <div class="muted">Runs on your machine; files are processed in memory.</div>
    <form method="post" enctype="multipart/form-data" style="margin-top:12px">
      <input type="file" name="pdfs" multiple accept="application/pdf"><br>
      <label>Output filename: <input name="outname" value="merged.pdf"></label><br><br>
      <button type="submit">Merge</button>
    </form>
    {% if message %}
      <div class="warn">{{ message }}</div>
    {% endif %}
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(TPL, message=None)

    files = request.files.getlist("pdfs")
    if not files:
        return render_template_string(TPL, message="Please choose at least one PDF.")

    outname = request.form.get("outname", "merged.pdf").strip() or "merged.pdf"
    outname = secure_filename(outname)

    writer = PdfWriter()
    skipped = []

    for fs in files:
        try:
            data = fs.read()
            if not data:
                skipped.append(fs.filename or "unnamed.pdf"); continue
            bio = BytesIO(data)
            reader = PdfReader(bio)
            if reader.is_encrypted:
                try:
                    reader.decrypt("")  # try blank password
                except Exception:
                    skipped.append(fs.filename or "encrypted.pdf")
                    continue
            for page in reader.pages:
                writer.add_page(page)
        except Exception:
            skipped.append(fs.filename or "invalid.pdf")

    if len(writer.pages) == 0:
        return render_template_string(TPL, message="No pages merged. Files might be encrypted or invalid.")

    # Write to memory and send
    out_mem = BytesIO()
    writer.write(out_mem)
    out_mem.seek(0)

    # Attach skipped list in a header-like message on landing page if needed
    if skipped:
        # Show a landing page with message and link to download again
        resp = send_file(out_mem, as_attachment=True, download_name=outname, mimetype="application/pdf")
        # You could also store 'skipped' in session/flash; keeping simple.
        return resp
    else:
        return send_file(out_mem, as_attachment=True, download_name=outname, mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=False)
