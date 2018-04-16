import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import url2pathname
import cgi
import mimetypes
import markdown
from markdown.extensions.toc import TocExtension

'''

ROPy Wiki
Written by Graham Sutherland (gsuberland)
Inspired by sqshr's mikiwiki - https://github.com/sqshr/mikiwiki

'''

sitedir = ".\\wiki"
page_template_path = ".\\pagetemplate.html"
combined_css_path = ".\\combined.css"


def readfile(filename):
    f = open(filename, 'r')
    contents = f.read()
    f.close()
    return contents


class RequestHandler(BaseHTTPRequestHandler):
    def handle_css(self):
        # when we request a CSS file, always return the combined CSS file
        self.send_response(200)
        self.send_header('Content-Type', 'text/css; charset=UTF-8')
        self.send_header('Cache-Control', 'public, max-age=0')
        self.end_headers()
        response = readfile(combined_css_path)
        self.wfile.write(response.encode('utf-8'))

    def handle_404(self):
        self.send_response(404)
        self.send_header('Content-Type', 'text/css; charset=UTF-8')
        self.end_headers()
        self.wfile.write('404'.encode('utf-8'))

    def handle_image(self, path, type):
        self.send_header('Content-Type', type)
        self.end_headers()
        # read the binary image file
        f = open(path, 'rb')
        image_data = f.read()
        f.close()
        # write it to the client
        self.wfile.write(image_data)

    def handle_page_render(self, content, title):
        self.send_header('Content-Type', 'text/html; charset=UTF-8')
        self.end_headers()
        # create a markdown engine with the table of contents extension enabled
        md = markdown.Markdown(extensions=[TocExtension(title=title)])
        template = readfile(page_template_path)     # html template for the page
        body = md.convert(content)                  # rendered HTML of the markdown
        toc = md.toc                                # table of contents HTML
        # place the above vars into the template data
        response = template.replace('%%TITLE%%', title).replace('%%BODY%%', body).replace('%%TOC%%', toc)
        # write the response out to the client
        self.wfile.write(response.encode('utf-8'))

    def handle_page(self, path, title):
        # get markdown content
        content = readfile(path)
        # render the markdown result
        self.handle_page_render(content, title)

    def handle_dir(self, path):
        # directory listing. first enumerate the dir...
        ls = sorted(os.listdir(path), key=str.lower)
        directories = []
        files = []
        for item in ls:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                directories.append((item_path, item))
            elif os.path.isfile(item_path):
                files.append((item_path, item))
        # now generate markdown for the directory
        content = "## Directories\n\n"
        for directory_path, directory in directories:
            content += "* [" + directory + "](" + os.path.relpath(directory_path, sitedir) + ")\n"
        content += "## Files\n\n"
        for file_path, file in files:
            content += "* [" + file + "](" + os.path.relpath(file_path, sitedir) + ")\n"
        # render the markdown result
        title = os.path.relpath(path, sitedir)
        if title == '.':
            title = "/"
        else:
            title = "/" + title
        self.handle_page_render(content, title)

    def quote_line(self, line, term):
        index_l = line.lower().index(term.lower())
        return line[:index_l] + "**" + line[index_l:index_l + len(term)] + "**" + line[index_l + len(term):]

    def handle_search(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
        term = ""
        if 'term' in form:
            term = form['term'].value
        term = str.lower(term)
        results_dirname = []
        results_filename = []
        results_contents = []
        if term != "":
            for root, dirs, files in os.walk(os.path.abspath(sitedir)):
                for name in dirs:
                    if term in str.lower(name):
                        results_dirname.append(os.path.relpath(os.path.join(root, name), os.path.abspath(sitedir)))
                for name in files:
                    if term in str.lower(name):
                        results_filename.append(os.path.relpath(os.path.join(root, name), os.path.abspath(sitedir)))
                for name in files:
                    line_number = 0
                    filepath = os.path.join(root, name)
                    guessed_type, guessed_encoding = mimetypes.guess_type(filepath)
                    if guessed_type is None or ('image' not in guessed_type and 'binary' not in guessed_type):
                        try:
                            for line in open(filepath):
                                if term in str.lower(line):
                                    results_contents.append((name, line_number, line))
                                line_number += 1
                        except:
                            print("Search couldn't read " + filepath)
        content = "# Search results for " + term + "\n"
        if len(results_dirname) == 0 and len(results_filename) == 0 and len(results_contents) == 0:
            content += "No results found."
        else:
            if len(results_dirname) > 0:
                content += "## Directory names\n"
                for dirname in results_dirname:
                    content += "* [" + dirname + "](" + dirname + ")\n"
            if len(results_filename) > 0:
                content += "## File names\n"
                for filename in results_filename:
                    content += "* [" + filename + "](" + filename + ")\n"
            if len(results_contents) > 0:
                content += "## File contents\n"
                for filename, line_number, line in results_contents:
                    content += "[" + filename + "](" + filename + ") line " + str(line_number) + ":\n\n"
                    content += " > " + self.quote_line(line, term) + "\n\n"
        self.handle_page_render(content, term)

    def do_GET(self):
        local_file_path = sitedir+url2pathname(self.path)
        if local_file_path.endswith('.css'):
            self.handle_css()
        else:
            if not os.path.exists(local_file_path):
                self.handle_404()
            else:
                self.send_response(200)
                if os.path.isfile(local_file_path):
                    # first try to guess what mime type the target file is
                    guessed_type, guessed_encoding = mimetypes.guess_type(local_file_path)
                    if guessed_type is not None and 'image' in guessed_type:
                        # if we guessed a type and that type is an image, return it as a binary file
                        self.handle_image(local_file_path, guessed_type)
                    else:
                        # we didn't detect the target file type as an image, so just assume this is markdown
                        page_title = os.path.splitext(os.path.basename(url2pathname(self.path)))[0]
                        self.handle_page(local_file_path, page_title)
                else:
                    self.handle_dir(local_file_path)

    def do_POST(self):
        if self.path == '/search':
            self.send_response(200)
            self.handle_search()
        else:
            self.handle_404()


def run():
    serveraddr = ('localhost', 8080)
    server = HTTPServer(serveraddr, RequestHandler)
    print("ROPyWiki started")
    server.serve_forever()

if __name__ == "__main__":
    run()
