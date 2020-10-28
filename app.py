from itertools import islice

from flask import Flask, render_template, request, redirect, url_for, session

from SpotifyPlaylistAnalyser import spotify, get_playlist_ids_names, get_top_artists, get_duplicates

app = Flask(__name__)
app.secret_key = b"\xf6\xa7\xc09p\x86\xb6\x87\x9a\x95o\x08K/C\xef"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        username = session.get("username")
        max_playlists = session.get("max_playlists")

        return render_template(
            "index.html", 
            username=username, 
            max_playlists=max_playlists
        )
    elif request.method == "POST":
        session["username"] = request.form["username"]
        session["max_playlists"] = int(request.form["max_playlists"])

        return redirect(url_for("playlists"))
    else:
        return f"Unhandled method: {request.method}"


@app.route("/playlists", methods=["GET", "POST"])
def playlists():
    if request.method == "GET":
        username = session.get("username")

        if username:
            max_playlists = session.get("max_playlists") or 10
            ids_names = list(islice(get_playlist_ids_names(username), max_playlists))

            return render_template(
                "playlists.html", 
                username=username,
                max_playlists=max_playlists,
                ids_names=ids_names
            )
        else:
            return redirect(url_for("index"))
    elif request.method == "POST":
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
    else:
        return f"Unhandled method: {request.method}"


@app.route("/analyse", methods=["GET", "POST"])
def analyse():
    if request.method == "GET":
        analyse_id_names = session.get("analyse_id_names")

        if analyse_id_names:
            top_artists = []
            duplicate_tracks = []

            for p_id, p_name in analyse_id_names:
                tracks = spotify.playlist_tracks(p_id)

                artists, count = get_top_artists(tracks)

                duplicates = get_duplicates(tracks)

                if artists:
                    top_artists.append([p_name, artists, count])
                
                if duplicates:
                    duplicates.sort(key=lambda x: x["count"], reverse=True)
                    duplicate_tracks.append([p_name, duplicates])

            top_artists.sort(key=lambda x: x[2], reverse=True)
            duplicate_tracks.sort(key=lambda x: x[1][0]["count"], reverse=True)

            return render_template(
                "analyse.html", 
                top_artists=top_artists,
                duplicate_tracks=duplicate_tracks
            )
        else:
            return redirect(url_for("playlists"))
    elif request.method == "POST":
        return redirect(url_for("playlists"))
    else:
        return f"Unhandled method: {request.method}"


if __name__ == '__main__':
    app.run(debug=True)
    
    session.clear()
