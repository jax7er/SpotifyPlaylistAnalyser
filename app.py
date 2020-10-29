from itertools import islice

from flask import Flask, redirect, render_template, request, session, url_for

from SpotifyPlaylistAnalyser import (get_duplicates, get_playlist_ids_names,
                                     get_top_artists, spotify)

app = Flask(__name__)

# required for the session signed cookie
app.secret_key = b"\xf6\xa7\xc09p\x86\xb6\x87\x9a\x95o\x08K/C\xef"


def handle_method(**methods_functions):
    """
    helper function for checking the HTTP method and returning an error message when it is not recognised

    methods_functions: Dict[http_method: str, function: Callable]
    """

    function = methods_functions.get(request.method.lower())

    if function:
        return function()
    else:
        return f"Unhandled method: {request.method}, please go back"


@app.route("/", methods=["GET", "POST"])
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
    
    def post():
        session["username"] = request.form["username"]
        session["max_playlists"] = int(request.form["max_playlists"] or 10)

        return redirect(url_for("playlists"))
    
    return handle_method(get=get, post=post)


@app.route("/playlists", methods=["GET", "POST"])
def playlists():
    """
    Displays a user's public playlists
    Allows user to select which playlists to include in the analysis and buttons to continue to analysis or return to selecting the username
    """

    def get():
        username = session.get("username")

        if username:
            # default max_playlists to 10 if not already in the session
            session["max_playlists"] = session.get("max_playlists", 10)

            max_playlists = session.get("max_playlists")
            ids_names = list(islice(
                get_playlist_ids_names(username), 
                max_playlists
            ))

            return render_template(
                "playlists.html", 
                username=username,
                max_playlists=max_playlists,
                ids_names=ids_names
            )
        else:
            return redirect(url_for("index"))

    def post():
        # get all the checkbox names that are checked
        analyse_id_names = [
            id_name.split("_", 1)
            for id_name, on in request.form.items()
            if on == "on"
        ]

        if analyse_id_names:
            session["analyse_id_names"] = analyse_id_names

            return redirect(url_for("analyse"))
        else:
            return redirect(url_for("playlists"))
    
    return handle_method(get=get, post=post)


@app.route("/analyse", methods=["GET", "POST"])
def analyse():
    """
    Display the analysis
    Shows the user the results of all the analyses performed on the selected playlists, if there are no results the section is not shown
    """

    def get():
        analyse_id_names = session.get("analyse_id_names")

        if analyse_id_names:
            top_artists = []
            duplicate_tracks = []

            for p_id, p_name in analyse_id_names:
                tracks = spotify.playlist_tracks(p_id)

                artists, count = get_top_artists(tracks)

                duplicates = get_duplicates(tracks)

                if artists:
                    top_artists.append({
                        "playlist": p_name, 
                        "artists": artists, 
                        "count": count
                    })
                
                if duplicates:
                    # descending order of track count
                    duplicates.sort(key=lambda x: x["count"], reverse=True)

                    duplicate_tracks.append((p_name, duplicates))

            # descending order of track count
            top_artists.sort(key=lambda x: x["count"], reverse=True)
            duplicate_tracks.sort(key=lambda x: x[1][0]["count"], reverse=True)

            return render_template(
                "analyse.html", 
                top_artists=top_artists,
                duplicate_tracks=duplicate_tracks
            )
        else:
            return redirect(url_for("playlists"))
    
    def post():
        return redirect(url_for("playlists"))
        
    return handle_method(get=get, post=post)


if __name__ == '__main__':
    app.run(debug=True)
