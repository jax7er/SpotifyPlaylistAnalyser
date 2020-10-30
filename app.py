from flask import Flask, redirect, render_template, request, session, url_for

from SpotifyPlaylistAnalyser import AnalyseThread, LoadThread

app = Flask(__name__)

# required for the session signed cookie
app.secret_key = b"\xf6\xa7\xc09p\x86\xb6\x87\x9a\x95o\x08K/C\xef"

load_thread: LoadThread = None
analyse_thread: AnalyseThread = None


def handle_request(**methods_functions):
    """
    helper function for handling the HTTP method and returning an error message when it is not recognised

    methods_functions: Dict[http_method: str, function: Callable]
    """

    function = methods_functions.get(request.method)

    return function() if function else (
        f"Unhandled HTTP method: {request.method}, "
        f"must be one of: {', '.join(methods_functions)}"
    )


@app.route("/")
def index():
    """
    Home page
    Contains the form to enter the user's username and maximum number of playlists to analyse
    """

    def get():
        username = session.get("username")
        max_playlists = session.get("max_playlists")

        return render_template(
            "index.html",
            username=username, 
            max_playlists=max_playlists
        )
    
    return handle_request(GET=get)


@app.route("/loading", methods=["POST"])
def loading():
    def post():
        username = request.form.get("username")

        if username:
            global load_thread

            max_playlists = int(request.form.get("max_playlists", 10))
            
            session["username"] = username
            session["max_playlists"] = max_playlists
            
            load_thread = LoadThread(username, max_playlists)
            load_thread.start()

            return render_template(
                "async.html",
                message=f"Loading up to {max_playlists} playlists...",
                redirect_url=url_for("playlists")
            )
        else:
            return redirect(url_for("index"))
    
    return handle_request(POST=post)


@app.route("/playlists")
def playlists():
    """
    Displays a user's public playlists
    Allows user to select which playlists to include in the analysis and buttons to continue to analysis or return to selecting the username
    """

    def get():
        global load_thread

        if load_thread is not None:
            username = session.get("username")
            playlists = load_thread.join()

            load_thread = None

            return render_template(
                "playlists.html",
                username=username,
                playlists=playlists
            )
        else:
            return redirect(url_for("index"))
    
    return handle_request(GET=get)


@app.route("/processing", methods=["POST"])
def processing():
    def post():
        # get all the checkbox names that are checked
        analyse_ids_names = list(request.form.items())

        if analyse_ids_names:            
            global analyse_thread
            
            analyse_thread = AnalyseThread(analyse_ids_names)
            analyse_thread.start()

            return render_template(
                "async.html",
                message=f"Processing {len(analyse_ids_names)} playlists...",
                redirect_url=url_for("analysis")
            )
        else:
            return redirect(url_for("playlists"))
    
    return handle_request(POST=post)


@app.route("/analysis")
def analysis():
    """
    Display the analysis
    Shows the user the results of all the analyses performed on the selected playlists, if there are no results the section is not shown
    """

    def get():
        global analyse_thread

        if analyse_thread is not None:
            top_artists, duplicate_tracks = analyse_thread.join()

            analyse_thread = None

            return render_template(
                "analysis.html",
                top_artists=top_artists,
                duplicate_tracks=duplicate_tracks
            )
        else:
            return redirect(url_for("playlists"))
        
    return handle_request(GET=get)


if __name__ == '__main__':
    app.run(debug=True) # local debug server
    # app.run(host="0.0.0.0") # externally visible server
