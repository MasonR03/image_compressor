import io
import os
import zipfile
from flask import Flask, render_template, request, redirect, url_for, flash, send_file # type: ignore
from PIL import Image

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the list of uploaded files.
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            flash("Please upload at least one image file.")
            return redirect(url_for('index'))

        # Create an in-memory bytes buffer for the ZIP archive.
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_archive:
            for file in files:
                if file.filename == '':
                    continue  # Skip empty fields

                try:
                    # Open the uploaded image file using Pillow.
                    image = Image.open(file)
                    output_buffer = io.BytesIO()

                    # Determine compression and file extension.
                    if image.format == "JPEG":
                        image.save(output_buffer, format="JPEG", quality=20, optimize=True)
                        ext = ".jpg"
                    elif image.format == "PNG":
                        image.save(output_buffer, format="PNG", optimize=True)
                        ext = ".png"
                    else:
                        # Convert any other image format to JPEG.
                        image.convert("RGB").save(output_buffer, format="JPEG", quality=20, optimize=True)
                        ext = ".jpg"

                    output_buffer.seek(0)

                    # Prepare a filename for the compressed image.
                    base_name = os.path.splitext(file.filename)[0]
                    compressed_filename = f"{base_name}{ext}"

                    # Write the compressed image to the ZIP archive.
                    zip_archive.writestr(compressed_filename, output_buffer.read())
                except Exception as e:
                    print(f"Error processing file '{file.filename}': {e}")
                    flash(f"Error processing file '{file.filename}'. See server logs for details.")
                    continue

        # Ensure the buffer's position is at the beginning.
        zip_buffer.seek(0)

        # Return the ZIP file as a download.
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='compressed_images.zip'
        )

    return render_template('index.html')


if __name__ == '__main__':
    # Listen on all interfaces so the container port is accessible externally.
    app.run(host='0.0.0.0', port=4042, debug=True)
