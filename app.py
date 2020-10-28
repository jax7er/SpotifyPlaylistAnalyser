from itertools import islice

from flask import Flask, render_template, request, redirect

from SpotifyPlaylistAnalyser import spotify, get_playlist_ids_names, get_top_artists

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    elif request.method == "POST":
        return redirect(f"playlists/{request.form['username']}")
    else:
        return f"Unhandled method: {request.method}"


@app.route("/playlists/<username>", methods=["GET", "POST"])
def playlists(username: str):
    if request.method == "GET":
        ids_names_gen = get_playlist_ids_names(username)

        ids_names = list(islice(ids_names_gen, 10))

        return render_template("playlists.html", username=username, ids_names=ids_names)
    elif request.method == "POST":
        return render_template("index.html")
    else:
        return f"Unhandled method: {request.method}"


@app.route("/analyse/<username>", methods=["GET", "POST"])
def analyse(username: str):
    if request.method == "GET":
        return redirect("/")
    elif request.method == "POST":
        analyse_ids = [
            p_id
            for p_id, on in request.form.items()
            if on == "on"
        ]

        data = []
        for p_id in analyse_ids:
            tracks = spotify.playlist_tracks(p_id)

            artists, count = get_top_artists(tracks)

            data.append([p_id, ", ".join(artists), count])

        data.sort(key=lambda x: x[2], reverse=True)

        return render_template("analyse.html", username=username, data=data)
    else:
        return f"Unhandled method: {request.method}"


if __name__ == '__main__':
    app.run(debug=True)
